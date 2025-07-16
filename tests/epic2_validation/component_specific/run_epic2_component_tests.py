"""
Epic 2 Component Tests Runner.

This script orchestrates and executes all Epic 2 component-specific tests,
providing comprehensive reporting and results management.

Features:
- Runs all component test suites
- Provides comprehensive test reporting
- Supports selective test execution
- Generates detailed performance metrics
- Handles test failures gracefully
- Provides summary statistics
"""

import os
import sys
import time
import logging
import argparse
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from epic2_component_test_utilities import (
    ComponentTestResult,
    ComponentPerformanceMetrics,
    create_component_test_environment,
)

logger = logging.getLogger(__name__)


class ComponentTestSuite:
    """Main test suite coordinator for Epic 2 component testing."""

    def __init__(self):
        self.test_environment = create_component_test_environment()
        self.results = {}
        self.start_time = None
        self.end_time = None

        # Component test modules
        self.component_modules = {
            "vector_indices": "test_epic2_vector_indices",
            "fusion_strategies": "test_epic2_fusion_strategies",
            "rerankers": "test_epic2_rerankers",
            "sparse_retrievers": "test_epic2_sparse_retrievers",
        }

    def run_all_tests(
        self, selected_components: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run all component tests or selected subset."""
        logger.info("🚀 Starting Epic 2 Component Test Suite")
        self.start_time = time.time()

        components_to_test = selected_components or list(self.component_modules.keys())

        for component_name in components_to_test:
            if component_name not in self.component_modules:
                logger.warning(f"Unknown component: {component_name}")
                continue

            logger.info(f"\n" + "=" * 60)
            logger.info(f"🧪 Running {component_name} tests...")
            logger.info("=" * 60)

            try:
                component_results = self._run_component_tests(component_name)
                self.results[component_name] = component_results

                # Summary for this component
                passed = sum(1 for r in component_results if r.success)
                total = len(component_results)
                logger.info(f"✅ {component_name}: {passed}/{total} tests passed")

            except Exception as e:
                logger.error(f"❌ Failed to run {component_name} tests: {e}")
                logger.error(traceback.format_exc())
                self.results[component_name] = []

        self.end_time = time.time()

        # Generate comprehensive report
        return self._generate_final_report()

    def _run_component_tests(self, component_name: str) -> List[ComponentTestResult]:
        """Run tests for a specific component."""
        module_name = self.component_modules[component_name]

        try:
            # Import the test module
            test_module = __import__(module_name, fromlist=[""])

            # Get the test runner function
            runner_function_name = f"run_{component_name}_tests"
            if hasattr(test_module, runner_function_name):
                runner_function = getattr(test_module, runner_function_name)
                return runner_function()
            else:
                logger.error(
                    f"No runner function {runner_function_name} found in {module_name}"
                )
                return []

        except ImportError as e:
            logger.error(f"Failed to import {module_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error running {component_name} tests: {e}")
            return []

    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final test report."""
        total_execution_time = (
            self.end_time - self.start_time if self.end_time and self.start_time else 0
        )

        # Aggregate statistics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        component_summaries = {}

        for component_name, results in self.results.items():
            passed = sum(1 for r in results if r.success)
            failed = len(results) - passed

            total_tests += len(results)
            total_passed += passed
            total_failed += failed

            # Calculate component performance metrics
            component_latencies = [
                r.metrics.latency_ms for r in results if r.metrics.latency_ms > 0
            ]
            avg_latency = (
                sum(component_latencies) / len(component_latencies)
                if component_latencies
                else 0
            )

            component_summaries[component_name] = {
                "total_tests": len(results),
                "passed": passed,
                "failed": failed,
                "success_rate": (passed / len(results) * 100) if results else 0,
                "avg_latency_ms": avg_latency,
                "failed_tests": [
                    {"name": r.test_name, "error": r.error_message}
                    for r in results
                    if not r.success
                ],
            }

        overall_success_rate = (
            (total_passed / total_tests * 100) if total_tests > 0 else 0
        )

        report = {
            "execution_info": {
                "start_time": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)
                ),
                "end_time": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(self.end_time)
                ),
                "total_execution_time_seconds": total_execution_time,
                "components_tested": list(self.results.keys()),
            },
            "summary": {
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "overall_success_rate": overall_success_rate,
                "components_tested": len(self.results),
            },
            "component_results": component_summaries,
            "detailed_results": {
                component_name: [
                    {
                        "test_name": r.test_name,
                        "success": r.success,
                        "latency_ms": r.metrics.latency_ms,
                        "error_message": r.error_message,
                        "details": r.details,
                    }
                    for r in results
                ]
                for component_name, results in self.results.items()
            },
        }

        return report

    def save_results(
        self, report: Dict[str, Any], output_file: Optional[str] = None
    ) -> str:
        """Save test results to file."""
        if output_file is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f"epic2_component_test_results_{timestamp}.json"

        output_path = Path(output_file)

        try:
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"📄 Test results saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return ""

    def print_summary_report(self, report: Dict[str, Any]):
        """Print formatted summary report to console."""
        print("\n" + "=" * 80)
        print("🎯 EPIC 2 COMPONENT TEST SUITE SUMMARY")
        print("=" * 80)

        # Execution info
        exec_info = report["execution_info"]
        print(f"📅 Execution Time: {exec_info['start_time']} - {exec_info['end_time']}")
        print(
            f"⏱️  Total Duration: {exec_info['total_execution_time_seconds']:.1f} seconds"
        )
        print(f"🧪 Components Tested: {', '.join(exec_info['components_tested'])}")

        print("\n" + "-" * 60)
        print("📊 OVERALL RESULTS")
        print("-" * 60)

        # Overall summary
        summary = report["summary"]
        print(f"✅ Total Tests Passed: {summary['total_passed']}")
        print(f"❌ Total Tests Failed: {summary['total_failed']}")
        print(f"📈 Overall Success Rate: {summary['overall_success_rate']:.1f}%")

        # Component breakdown
        print("\n" + "-" * 60)
        print("🔧 COMPONENT BREAKDOWN")
        print("-" * 60)

        for component_name, component_data in report["component_results"].items():
            status_emoji = (
                "✅"
                if component_data["success_rate"] == 100
                else "⚠️" if component_data["success_rate"] >= 80 else "❌"
            )
            print(f"{status_emoji} {component_name.replace('_', ' ').title()}:")
            print(
                f"   Tests: {component_data['passed']}/{component_data['total_tests']} passed"
            )
            print(f"   Success Rate: {component_data['success_rate']:.1f}%")
            print(f"   Avg Latency: {component_data['avg_latency_ms']:.1f}ms")

            if component_data["failed_tests"]:
                print(f"   Failed Tests:")
                for failed_test in component_data["failed_tests"]:
                    print(f"     - {failed_test['name']}: {failed_test['error']}")
            print()

        # Performance insights
        print("-" * 60)
        print("⚡ PERFORMANCE INSIGHTS")
        print("-" * 60)

        component_latencies = []
        for component_name, component_data in report["component_results"].items():
            if component_data["avg_latency_ms"] > 0:
                component_latencies.append(
                    (component_name, component_data["avg_latency_ms"])
                )

        if component_latencies:
            component_latencies.sort(key=lambda x: x[1])
            print("Fastest to Slowest Components:")
            for component_name, latency in component_latencies:
                print(
                    f"  🚀 {component_name.replace('_', ' ').title()}: {latency:.1f}ms"
                )

        print("\n" + "=" * 80)

        # Final verdict
        if summary["overall_success_rate"] >= 95:
            print("🎉 EXCELLENT: Epic 2 components are performing exceptionally well!")
        elif summary["overall_success_rate"] >= 85:
            print("✅ GOOD: Epic 2 components are performing well with minor issues.")
        elif summary["overall_success_rate"] >= 70:
            print("⚠️  WARNING: Epic 2 components have some significant issues.")
        else:
            print(
                "❌ CRITICAL: Epic 2 components have major issues requiring attention."
            )

        print("=" * 80)


def main():
    """Main entry point for component testing."""
    parser = argparse.ArgumentParser(description="Epic 2 Component Test Suite")

    parser.add_argument(
        "--components",
        nargs="+",
        choices=[
            "all",
            "vector_indices",
            "fusion_strategies",
            "rerankers",
            "sparse_retrievers",
        ],
        default=["all"],
        help="Specific components to test (default: all)",
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output file for test results (default: auto-generated)",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    parser.add_argument(
        "--quiet", action="store_true", help="Suppress detailed output (summary only)"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = (
        logging.DEBUG
        if args.verbose
        else logging.INFO if not args.quiet else logging.WARNING
    )
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run tests
    test_suite = ComponentTestSuite()

    # Handle "all" components choice
    if "all" in args.components:
        components_to_test = [
            "vector_indices",
            "fusion_strategies",
            "rerankers",
            "sparse_retrievers",
        ]
    else:
        components_to_test = args.components

    try:
        report = test_suite.run_all_tests(components_to_test)

        # Save results
        if args.output or not args.quiet:
            results_file = test_suite.save_results(report, args.output)

        # Print summary
        if not args.quiet:
            test_suite.print_summary_report(report)

        # Exit with appropriate code
        exit_code = 0 if report["summary"]["overall_success_rate"] >= 90 else 1

        if exit_code == 0:
            logger.info("🎉 All component tests completed successfully!")
        else:
            logger.warning(
                "⚠️  Some component tests failed - check the report for details"
            )

        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.info("Component testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Component testing failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
