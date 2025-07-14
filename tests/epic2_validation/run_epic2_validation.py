"""
Epic 2 Validation Runner.

This script orchestrates the complete Epic 2 validation suite including:
- Multi-backend infrastructure validation
- Graph integration validation
- Neural reranking validation
- Complete system integration validation
- Performance benchmarking
- Quality assessment

Usage:
    python run_epic2_validation.py --comprehensive
    python run_epic2_validation.py --quick
    python run_epic2_validation.py --performance-only
    python run_epic2_validation.py --quality-only
"""

import argparse
import logging
import time
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import validation modules
from test_multi_backend_validation import MultiBackendValidator
from test_graph_integration_validation import GraphIntegrationValidator
from test_neural_reranking_validation import NeuralRerankingValidator
from test_epic2_integration_validation import Epic2IntegrationValidator
from test_epic2_performance_validation import Epic2PerformanceValidator
from test_epic2_quality_validation import Epic2QualityValidator


class NumpyJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy data types."""

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        return super().default(obj)


class Epic2ValidationRunner:
    """
    Comprehensive Epic 2 validation runner.

    Orchestrates all validation components for thorough Epic 2 system validation.
    """

    def __init__(self, output_dir: str = "validation_results"):
        """Initialize validation runner."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize all validators
        self.validators = {
            "multi_backend": MultiBackendValidator(),
            "graph_integration": GraphIntegrationValidator(),
            "neural_reranking": NeuralRerankingValidator(),
            "epic2_integration": Epic2IntegrationValidator(),
            "performance": Epic2PerformanceValidator(),
            "quality": Epic2QualityValidator(),
        }

        self.validation_results = {}
        self.overall_metrics = {}

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete Epic 2 validation suite."""
        logger.info("Starting comprehensive Epic 2 validation...")

        start_time = time.time()

        # Run all validation modules
        for validator_name, validator in self.validators.items():
            logger.info(f"Running {validator_name} validation...")

            try:
                validation_start = time.time()
                results = validator.run_all_validations()
                validation_time = time.time() - validation_start

                results["validation_time_seconds"] = validation_time
                self.validation_results[validator_name] = results

                logger.info(
                    f"  {validator_name}: {results['overall_score']:.1f}% "
                    f"({results['passed_tests']}/{results['total_tests']} tests) "
                    f"in {validation_time:.2f}s"
                )

            except Exception as e:
                logger.error(f"  {validator_name} validation failed: {str(e)}")
                self.validation_results[validator_name] = {
                    "overall_score": 0,
                    "passed_tests": 0,
                    "total_tests": 0,
                    "validation_errors": [f"Critical failure: {str(e)}"],
                    "validation_time_seconds": 0,
                }

        total_time = time.time() - start_time

        # Calculate overall metrics
        self._calculate_overall_metrics(total_time)

        # Save results
        self._save_results()

        return {
            "validation_results": self.validation_results,
            "overall_metrics": self.overall_metrics,
        }

    def run_quick_validation(self) -> Dict[str, Any]:
        """Run quick validation focusing on critical tests."""
        logger.info("Starting quick Epic 2 validation...")

        # Run subset of critical tests
        critical_validators = ["epic2_integration", "performance"]

        start_time = time.time()

        for validator_name in critical_validators:
            if validator_name in self.validators:
                logger.info(f"Running {validator_name} validation...")

                try:
                    validation_start = time.time()
                    results = self.validators[validator_name].run_all_validations()
                    validation_time = time.time() - validation_start

                    results["validation_time_seconds"] = validation_time
                    self.validation_results[validator_name] = results

                    logger.info(
                        f"  {validator_name}: {results['overall_score']:.1f}% "
                        f"({results['passed_tests']}/{results['total_tests']} tests)"
                    )

                except Exception as e:
                    logger.error(f"  {validator_name} validation failed: {str(e)}")
                    self.validation_results[validator_name] = {
                        "overall_score": 0,
                        "passed_tests": 0,
                        "total_tests": 0,
                        "validation_errors": [f"Critical failure: {str(e)}"],
                    }

        total_time = time.time() - start_time
        self._calculate_overall_metrics(total_time)
        self._save_results()

        return {
            "validation_results": self.validation_results,
            "overall_metrics": self.overall_metrics,
        }

    def run_performance_validation(self) -> Dict[str, Any]:
        """Run performance-focused validation."""
        logger.info("Starting performance Epic 2 validation...")

        performance_validators = ["performance", "multi_backend"]

        start_time = time.time()

        for validator_name in performance_validators:
            if validator_name in self.validators:
                logger.info(f"Running {validator_name} validation...")

                try:
                    results = self.validators[validator_name].run_all_validations()
                    self.validation_results[validator_name] = results

                    logger.info(f"  {validator_name}: {results['overall_score']:.1f}%")

                except Exception as e:
                    logger.error(f"  {validator_name} validation failed: {str(e)}")
                    self.validation_results[validator_name] = {
                        "overall_score": 0,
                        "validation_errors": [f"Critical failure: {str(e)}"],
                    }

        total_time = time.time() - start_time
        self._calculate_overall_metrics(total_time)
        self._save_results()

        return {
            "validation_results": self.validation_results,
            "overall_metrics": self.overall_metrics,
        }

    def run_quality_validation(self) -> Dict[str, Any]:
        """Run quality-focused validation."""
        logger.info("Starting quality Epic 2 validation...")

        quality_validators = ["quality", "neural_reranking", "graph_integration"]

        start_time = time.time()

        for validator_name in quality_validators:
            if validator_name in self.validators:
                logger.info(f"Running {validator_name} validation...")

                try:
                    results = self.validators[validator_name].run_all_validations()
                    self.validation_results[validator_name] = results

                    logger.info(f"  {validator_name}: {results['overall_score']:.1f}%")

                except Exception as e:
                    logger.error(f"  {validator_name} validation failed: {str(e)}")
                    self.validation_results[validator_name] = {
                        "overall_score": 0,
                        "validation_errors": [f"Critical failure: {str(e)}"],
                    }

        total_time = time.time() - start_time
        self._calculate_overall_metrics(total_time)
        self._save_results()

        return {
            "validation_results": self.validation_results,
            "overall_metrics": self.overall_metrics,
        }

    def _calculate_overall_metrics(self, total_time: float):
        """Calculate overall validation metrics."""
        # Aggregate scores and test counts
        total_score = 0
        total_tests = 0
        total_passed = 0
        total_errors = []

        for validator_name, results in self.validation_results.items():
            if "overall_score" in results:
                total_score += results["overall_score"]
            if "total_tests" in results:
                total_tests += results["total_tests"]
            if "passed_tests" in results:
                total_passed += results["passed_tests"]
            if "validation_errors" in results:
                total_errors.extend(results["validation_errors"])

        # Calculate overall score
        overall_score = (
            total_score / len(self.validation_results) if self.validation_results else 0
        )

        # Determine portfolio readiness
        portfolio_status = (
            "PORTFOLIO_READY" if overall_score >= 90 else "NEEDS_IMPROVEMENT"
        )
        if overall_score >= 95:
            portfolio_status = "PORTFOLIO_EXCELLENT"
        elif overall_score < 70:
            portfolio_status = "PORTFOLIO_INCOMPLETE"

        # Performance summary
        performance_metrics = {}
        if "performance" in self.validation_results:
            perf_results = self.validation_results["performance"]
            if "test_results" in perf_results:
                performance_metrics = {
                    "latency_target_met": False,
                    "memory_target_met": False,
                    "cpu_target_met": False,
                }

                # Extract performance targets
                for test_name, test_result in perf_results["test_results"].items():
                    if "details" in test_result:
                        details = test_result["details"]
                        if "latency_target_met" in details:
                            performance_metrics["latency_target_met"] = details[
                                "latency_target_met"
                            ]
                        if "memory_target_met" in details:
                            performance_metrics["memory_target_met"] = details[
                                "memory_target_met"
                            ]
                        if "cpu_target_met" in details:
                            performance_metrics["cpu_target_met"] = details[
                                "cpu_target_met"
                            ]

        # Quality summary
        quality_metrics = {}
        if "quality" in self.validation_results:
            quality_results = self.validation_results["quality"]
            if "test_results" in quality_results:
                quality_metrics = {
                    "relevance_improvement": False,
                    "risc_v_quality": False,
                    "consistency": False,
                }

                # Extract quality targets
                for test_name, test_result in quality_results["test_results"].items():
                    if "details" in test_result and test_result.get("passed", False):
                        if "improvement" in test_name:
                            quality_metrics["relevance_improvement"] = True
                        if "risc_v" in test_name:
                            quality_metrics["risc_v_quality"] = True
                        if "consistency" in test_name:
                            quality_metrics["consistency"] = True

        self.overall_metrics = {
            "overall_score": overall_score,
            "portfolio_status": portfolio_status,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_errors": len(total_errors),
            "validation_time_seconds": total_time,
            "validators_run": list(self.validation_results.keys()),
            "performance_metrics": performance_metrics,
            "quality_metrics": quality_metrics,
            "epic2_features_validated": {
                "multi_backend": "multi_backend" in self.validation_results,
                "graph_retrieval": "graph_integration" in self.validation_results,
                "neural_reranking": "neural_reranking" in self.validation_results,
                "complete_integration": "epic2_integration" in self.validation_results,
            },
        }

    def _save_results(self):
        """Save validation results to files."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # Save detailed results
        results_file = self.output_dir / f"epic2_validation_results_{timestamp}.json"
        with open(results_file, "w") as f:
            json.dump(
                {
                    "validation_results": self.validation_results,
                    "overall_metrics": self.overall_metrics,
                },
                f,
                indent=2,
                cls=NumpyJSONEncoder,
            )

        # Save summary report
        summary_file = self.output_dir / f"epic2_validation_summary_{timestamp}.txt"
        self._generate_summary_report(summary_file)

        logger.info(f"Results saved to {results_file}")
        logger.info(f"Summary saved to {summary_file}")

    def _generate_summary_report(self, summary_file: Path):
        """Generate human-readable summary report."""
        with open(summary_file, "w") as f:
            f.write("EPIC 2 VALIDATION SUMMARY REPORT\n")
            f.write("=" * 80 + "\n\n")

            # Overall metrics
            f.write(f"Overall Score: {self.overall_metrics['overall_score']:.1f}%\n")
            f.write(f"Portfolio Status: {self.overall_metrics['portfolio_status']}\n")
            f.write(
                f"Total Tests: {self.overall_metrics['total_passed']}/{self.overall_metrics['total_tests']}\n"
            )
            f.write(
                f"Validation Time: {self.overall_metrics['validation_time_seconds']:.2f}s\n\n"
            )

            # Epic 2 features validation status
            f.write("EPIC 2 FEATURES VALIDATION:\n")
            f.write("-" * 40 + "\n")
            for feature, validated in self.overall_metrics[
                "epic2_features_validated"
            ].items():
                status = "✅ VALIDATED" if validated else "❌ NOT TESTED"
                f.write(f"  {feature}: {status}\n")
            f.write("\n")

            # Performance metrics
            if self.overall_metrics["performance_metrics"]:
                f.write("PERFORMANCE TARGETS:\n")
                f.write("-" * 40 + "\n")
                for metric, met in self.overall_metrics["performance_metrics"].items():
                    status = "✅ MET" if met else "❌ NOT MET"
                    f.write(f"  {metric}: {status}\n")
                f.write("\n")

            # Quality metrics
            if self.overall_metrics["quality_metrics"]:
                f.write("QUALITY TARGETS:\n")
                f.write("-" * 40 + "\n")
                for metric, met in self.overall_metrics["quality_metrics"].items():
                    status = "✅ MET" if met else "❌ NOT MET"
                    f.write(f"  {metric}: {status}\n")
                f.write("\n")

            # Detailed results by validator
            f.write("DETAILED VALIDATION RESULTS:\n")
            f.write("-" * 40 + "\n")
            for validator_name, results in self.validation_results.items():
                f.write(f"\n{validator_name.upper()}:\n")
                f.write(f"  Score: {results.get('overall_score', 0):.1f}%\n")
                f.write(
                    f"  Tests: {results.get('passed_tests', 0)}/{results.get('total_tests', 0)}\n"
                )

                if results.get("validation_errors"):
                    f.write(f"  Errors:\n")
                    for error in results["validation_errors"][
                        :3
                    ]:  # Show first 3 errors
                        f.write(f"    - {error}\n")
                    if len(results["validation_errors"]) > 3:
                        f.write(
                            f"    ... and {len(results['validation_errors']) - 3} more\n"
                        )

            # Recommendations
            f.write("\nRECOMMENDations:\n")
            f.write("-" * 40 + "\n")

            if self.overall_metrics["overall_score"] >= 90:
                f.write("✅ Epic 2 system is ready for portfolio inclusion\n")
                f.write("✅ All major features are functional and meet targets\n")
            elif self.overall_metrics["overall_score"] >= 70:
                f.write("⚠️  Epic 2 system shows good progress but needs refinement\n")
                f.write(
                    "⚠️  Address performance or quality issues before portfolio inclusion\n"
                )
            else:
                f.write("❌ Epic 2 system requires significant improvements\n")
                f.write("❌ Major features are not functional or fail targets\n")

            f.write(f"\nGenerated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")


def main():
    """Main entry point for Epic 2 validation."""
    parser = argparse.ArgumentParser(description="Epic 2 Validation Runner")
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Run comprehensive validation suite",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick validation (critical tests only)",
    )
    parser.add_argument(
        "--performance-only",
        action="store_true",
        help="Run performance validation only",
    )
    parser.add_argument(
        "--quality-only", action="store_true", help="Run quality validation only"
    )
    parser.add_argument(
        "--output-dir",
        default="validation_results",
        help="Output directory for results",
    )

    args = parser.parse_args()

    # Default to comprehensive if no specific mode selected
    if not any(
        [args.comprehensive, args.quick, args.performance_only, args.quality_only]
    ):
        args.comprehensive = True

    # Create validation runner
    runner = Epic2ValidationRunner(args.output_dir)

    # Run validation based on selected mode
    try:
        if args.comprehensive:
            results = runner.run_comprehensive_validation()
        elif args.quick:
            results = runner.run_quick_validation()
        elif args.performance_only:
            results = runner.run_performance_validation()
        elif args.quality_only:
            results = runner.run_quality_validation()

        # Print summary
        print("\n" + "=" * 80)
        print("EPIC 2 VALIDATION COMPLETED")
        print("=" * 80)
        print(f"Overall Score: {runner.overall_metrics['overall_score']:.1f}%")
        print(f"Portfolio Status: {runner.overall_metrics['portfolio_status']}")
        print(
            f"Tests Passed: {runner.overall_metrics['total_passed']}/{runner.overall_metrics['total_tests']}"
        )
        print(
            f"Validation Time: {runner.overall_metrics['validation_time_seconds']:.2f}s"
        )

        if runner.overall_metrics["total_errors"] > 0:
            print(f"Errors: {runner.overall_metrics['total_errors']}")

        print(f"\nResults saved to: {args.output_dir}/")

        # Exit code based on success
        exit_code = 0 if runner.overall_metrics["overall_score"] >= 70 else 1
        return exit_code

    except Exception as e:
        logger.error(f"Epic 2 validation failed: {str(e)}")
        print(f"\n❌ Epic 2 validation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
