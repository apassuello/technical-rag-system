#!/usr/bin/env python3
"""
Quick Epic 2 Test Runner
========================

Simple test runner for basic Epic 2 validation.
Runs essential tests quickly without comprehensive validation.

Usage:
    python run_quick_epic2_test.py
    python run_quick_epic2_test.py --test configuration
    python run_quick_epic2_test.py --test subcomponent
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project root and epic2_validation to Python path
project_root = Path(__file__).parent.parent.parent
epic2_validation_dir = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(epic2_validation_dir))

# Import Epic 2 test modules
from tests.epic2_validation.test_epic2_configuration_validation_new import Epic2ConfigurationValidator
from tests.epic2_validation.test_epic2_subcomponent_integration_new import (
    Epic2SubComponentIntegrationValidator,
)
from tests.epic2_validation.epic2_test_utilities import Epic2TestEnvironment

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_environment_check():
    """Quick environment validation."""
    print("🔍 Checking Epic 2 test environment...")

    env_results = Epic2TestEnvironment.validate_environment()

    if env_results["overall"]["ready"]:
        print("✅ Environment ready for Epic 2 testing")
        return True
    else:
        print("❌ Environment issues detected:")
        for issue in env_results["overall"]["issues"]:
            print(f"  - {issue}")
        return False


def run_configuration_test():
    """Run configuration validation test."""
    print("\n🔧 Running configuration validation...")

    try:
        validator = Epic2ConfigurationValidator()
        results = validator.run_all_validations()

        score = results.get("overall_score", 0)
        passed = results.get("passed_tests", 0)
        total = results.get("total_tests", 0)

        if score >= 80:
            print(f"✅ Configuration validation: {score:.1f}% ({passed}/{total})")
        else:
            print(f"❌ Configuration validation: {score:.1f}% ({passed}/{total})")

            # Show first few errors
            if results.get("validation_errors"):
                print("  Issues:")
                for error in results["validation_errors"][:3]:
                    print(f"    - {error}")

        return score >= 80

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def run_subcomponent_test():
    """Run sub-component integration test."""
    print("\n🔗 Running sub-component integration...")

    try:
        validator = Epic2SubComponentIntegrationValidator()
        results = validator.run_all_validations()

        score = results.get("overall_score", 0)
        passed = results.get("passed_tests", 0)
        total = results.get("total_tests", 0)

        if score >= 80:
            print(f"✅ Sub-component integration: {score:.1f}% ({passed}/{total})")
        else:
            print(f"❌ Sub-component integration: {score:.1f}% ({passed}/{total})")

            # Show first few errors
            if results.get("validation_errors"):
                print("  Issues:")
                for error in results["validation_errors"][:3]:
                    print(f"    - {error}")

        return score >= 80

    except Exception as e:
        print(f"❌ Sub-component test failed: {e}")
        return False


def main():
    """Main entry point for quick Epic 2 test."""
    parser = argparse.ArgumentParser(description="Quick Epic 2 Test Runner")

    parser.add_argument(
        "--test",
        choices=["environment", "configuration", "subcomponent", "all"],
        default="all",
        help="Specific test to run",
    )

    args = parser.parse_args()

    print("🚀 Epic 2 Quick Test Runner")
    print("=" * 40)

    results = []

    # Environment check (always run)
    env_ok = run_environment_check()
    results.append(("Environment", env_ok))

    if not env_ok:
        print("\n❌ Environment not ready. Please fix issues before running tests.")
        sys.exit(1)

    # Run requested tests
    if args.test in ["configuration", "all"]:
        config_ok = run_configuration_test()
        results.append(("Configuration", config_ok))

    if args.test in ["subcomponent", "all"]:
        subcomp_ok = run_subcomponent_test()
        results.append(("Sub-component", subcomp_ok))

    # Summary
    print("\n📊 Quick Test Summary")
    print("-" * 30)

    passed_tests = sum(1 for _, result in results if result)
    total_tests = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")

    success_rate = (passed_tests / total_tests) * 100
    print(f"\nOverall: {success_rate:.1f}% ({passed_tests}/{total_tests})")

    if success_rate >= 100:
        print("🎉 All quick tests passed! Epic 2 basic functionality verified.")
        sys.exit(0)
    elif success_rate >= 80:
        print("✅ Most tests passed. Epic 2 mostly functional with minor issues.")
        sys.exit(0)
    else:
        print("❌ Multiple test failures. Epic 2 needs attention.")
        sys.exit(1)


if __name__ == "__main__":
    main()
