#!/usr/bin/env python3
"""Test runner for Epic 1 Phase 2 components.

Executes comprehensive test suite for Epic 1 Phase 2 multi-model adapters
following the test plan specifications.
"""

import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import json

# Test suite configuration
TEST_MODULES = [
    {
        "module": "test_openai_adapter",
        "description": "OpenAI Adapter Tests",
        "critical": True,
        "estimated_time": 120  # seconds
    },
    {
        "module": "test_mistral_adapter",
        "description": "Mistral Adapter Tests",
        "critical": True,
        "estimated_time": 100
    },
    {
        "module": "test_cost_tracker",
        "description": "Cost Tracking System Tests",
        "critical": True,
        "estimated_time": 150
    },
    {
        "module": "test_routing_strategies",
        "description": "Routing Strategy Tests",
        "critical": True,
        "estimated_time": 90
    },
    {
        "module": "test_adaptive_router",
        "description": "Adaptive Router Tests",
        "critical": True,
        "estimated_time": 180
    },
    {
        "module": "test_epic1_answer_generator",
        "description": "Epic1AnswerGenerator Integration Tests",
        "critical": True,
        "estimated_time": 200
    }
]


class TestRunner:
    """Test runner for Epic 1 Phase 2 test suite."""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        
        # Test execution options
        self.verbose = True
        self.stop_on_failure = False
        self.parallel_execution = False
        
    def run_single_test_module(self, test_module: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test module and return results."""
        module_name = test_module["module"]
        description = test_module["description"]
        
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Module: {module_name}")
        print(f"Estimated time: {test_module['estimated_time']}s")
        print(f"{'='*60}")
        
        # Build pytest command
        test_file = Path(__file__).parent / f"{module_name}.py"
        cmd = [
            sys.executable, "-m", "pytest", 
            str(test_file),
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "--durations=10",  # Show 10 slowest tests
            "--json-report",  # Generate JSON report
            f"--json-report-file=/tmp/{module_name}_report.json"
        ]
        
        if self.verbose:
            cmd.append("-s")  # Don't capture output
        
        # Execute test
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=not self.verbose,
                text=True,
                timeout=test_module['estimated_time'] * 2  # 2x safety margin
            )
            
            execution_time = time.time() - start_time
            
            # Parse results
            success = result.returncode == 0
            
            # Try to load JSON report for detailed results
            test_stats = self._parse_json_report(f"/tmp/{module_name}_report.json")
            
            return {
                "module": module_name,
                "description": description,
                "success": success,
                "execution_time": execution_time,
                "return_code": result.returncode,
                "stdout": result.stdout if result.stdout else "",
                "stderr": result.stderr if result.stderr else "",
                "test_stats": test_stats,
                "critical": test_module["critical"]
            }
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return {
                "module": module_name,
                "description": description,
                "success": False,
                "execution_time": execution_time,
                "return_code": -1,
                "stdout": "",
                "stderr": "Test execution timed out",
                "test_stats": {},
                "critical": test_module["critical"],
                "timeout": True
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "module": module_name,
                "description": description,
                "success": False,
                "execution_time": execution_time,
                "return_code": -2,
                "stdout": "",
                "stderr": str(e),
                "test_stats": {},
                "critical": test_module["critical"],
                "exception": True
            }
    
    def _parse_json_report(self, report_path: str) -> Dict[str, Any]:
        """Parse pytest JSON report if available."""
        try:
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            summary = report.get('summary', {})
            return {
                "total": summary.get('total', 0),
                "passed": summary.get('passed', 0),
                "failed": summary.get('failed', 0),
                "skipped": summary.get('skipped', 0),
                "errors": summary.get('error', 0),
                "duration": report.get('duration', 0)
            }
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return {}
    
    def print_test_summary(self, result: Dict[str, Any]) -> None:
        """Print summary for a single test module."""
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        critical = "🔴 CRITICAL" if result["critical"] else "🟡 STANDARD"
        
        print(f"\n{status} {critical} - {result['description']}")
        print(f"   Time: {result['execution_time']:.2f}s")
        
        if result["test_stats"]:
            stats = result["test_stats"]
            print(f"   Tests: {stats.get('passed', 0)} passed, {stats.get('failed', 0)} failed, {stats.get('skipped', 0)} skipped")
        
        if not result["success"]:
            print(f"   Return Code: {result['return_code']}")
            if result["stderr"]:
                print(f"   Error: {result['stderr'][:200]}..." if len(result["stderr"]) > 200 else f"   Error: {result['stderr']}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test modules in the suite."""
        print("\n🚀 Starting Epic 1 Phase 2 Test Suite")
        print(f"Total modules: {len(TEST_MODULES)}")
        print(f"Estimated total time: {sum(m['estimated_time'] for m in TEST_MODULES)}s")
        
        self.start_time = time.time()
        
        for test_module in TEST_MODULES:
            result = self.run_single_test_module(test_module)
            self.results.append(result)
            self.print_test_summary(result)
            
            # Update counters
            if result["test_stats"]:
                self.total_tests += result["test_stats"].get("total", 0)
                self.passed_tests += result["test_stats"].get("passed", 0)
                self.failed_tests += result["test_stats"].get("failed", 0)
                self.skipped_tests += result["test_stats"].get("skipped", 0)
            
            # Stop on critical failure if configured
            if self.stop_on_failure and not result["success"] and result["critical"]:
                print(f"\n🛑 Stopping execution due to critical failure in {result['module']}")
                break
        
        return self._generate_final_report()
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate final test execution report."""
        total_time = time.time() - self.start_time
        
        # Calculate success metrics
        successful_modules = sum(1 for r in self.results if r["success"])
        failed_modules = len(self.results) - successful_modules
        critical_failures = sum(1 for r in self.results if not r["success"] and r["critical"])
        
        # Overall success determination
        overall_success = critical_failures == 0
        
        report = {
            "overall_success": overall_success,
            "execution_time": total_time,
            "modules": {
                "total": len(TEST_MODULES),
                "passed": successful_modules,
                "failed": failed_modules,
                "critical_failures": critical_failures
            },
            "tests": {
                "total": self.total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "skipped": self.skipped_tests
            },
            "results": self.results
        }
        
        self._print_final_report(report)
        return report
    
    def _print_final_report(self, report: Dict[str, Any]) -> None:
        """Print comprehensive final report."""
        print("\n" + "="*80)
        print("🎯 EPIC 1 PHASE 2 TEST SUITE RESULTS")
        print("="*80)
        
        # Overall status
        status = "✅ SUCCESS" if report["overall_success"] else "❌ FAILURE"
        print(f"\nOverall Status: {status}")
        print(f"Total Execution Time: {report['execution_time']:.2f}s")
        
        # Module summary
        modules = report["modules"]
        print(f"\n📦 Module Summary:")
        print(f"   Total Modules: {modules['total']}")
        print(f"   Passed: {modules['passed']} ✅")
        print(f"   Failed: {modules['failed']} ❌")
        print(f"   Critical Failures: {modules['critical_failures']} 🔴")
        
        # Test summary
        tests = report["tests"]
        if tests["total"] > 0:
            success_rate = (tests["passed"] / tests["total"]) * 100
            print(f"\n🧪 Test Summary:")
            print(f"   Total Tests: {tests['total']}")
            print(f"   Passed: {tests['passed']} ({success_rate:.1f}%)")
            print(f"   Failed: {tests['failed']}")
            print(f"   Skipped: {tests['skipped']}")
        
        # Performance analysis
        print(f"\n⚡ Performance Analysis:")
        for result in self.results:
            perf_status = "🟢" if result["execution_time"] < result.get("estimated_time", float('inf')) else "🟡"
            print(f"   {perf_status} {result['module']}: {result['execution_time']:.2f}s")
        
        # Failed modules details
        failed_results = [r for r in self.results if not r["success"]]
        if failed_results:
            print(f"\n❌ Failed Modules Details:")
            for result in failed_results:
                critical = "🔴 CRITICAL" if result["critical"] else "🟡"
                print(f"   {critical} {result['module']} - {result['description']}")
                if result["stderr"]:
                    print(f"      Error: {result['stderr'][:100]}...")
        
        # Success criteria assessment
        print(f"\n📊 Success Criteria Assessment:")
        criteria = {
            "All critical tests passing": modules['critical_failures'] == 0,
            "Overall test success rate >95%": (tests["passed"] / max(tests["total"], 1)) > 0.95,
            "No module timeouts": not any(r.get("timeout", False) for r in self.results),
            "Performance targets met": all(r["execution_time"] < r.get("estimated_time", float('inf')) * 1.5 for r in self.results)
        }
        
        for criterion, met in criteria.items():
            status = "✅" if met else "❌"
            print(f"   {status} {criterion}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if not report["overall_success"]:
            if modules["critical_failures"] > 0:
                print("   🔥 Critical failures detected - must be resolved before Phase 2 completion")
            if tests["failed"] > 0:
                print("   🔧 Review failed test cases and fix underlying issues")
            print("   📋 Check test logs for detailed failure analysis")
        else:
            print("   🎉 All tests passing - Epic 1 Phase 2 ready for production")
            print("   📈 Consider running performance benchmarks for optimization")
        
        print("\n" + "="*80)


def main():
    """Main test execution entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Epic 1 Phase 2 test suite")
    parser.add_argument("--stop-on-failure", action="store_true", 
                       help="Stop execution on first critical failure")
    parser.add_argument("--quiet", action="store_true", 
                       help="Reduce output verbosity")
    parser.add_argument("--module", type=str, 
                       help="Run specific test module only")
    parser.add_argument("--save-report", type=str, 
                       help="Save detailed report to JSON file")
    
    args = parser.parse_args()
    
    # Configure test runner
    runner = TestRunner()
    runner.verbose = not args.quiet
    runner.stop_on_failure = args.stop_on_failure
    
    # Run tests
    if args.module:
        # Run single module
        test_module = next((m for m in TEST_MODULES if m["module"] == args.module), None)
        if not test_module:
            print(f"❌ Module '{args.module}' not found in test suite")
            print(f"Available modules: {', '.join(m['module'] for m in TEST_MODULES)}")
            sys.exit(1)
        
        result = runner.run_single_test_module(test_module)
        runner.results = [result]
        runner.print_test_summary(result)
        
        report = {
            "overall_success": result["success"],
            "execution_time": result["execution_time"],
            "modules": {"total": 1, "passed": 1 if result["success"] else 0, "failed": 0 if result["success"] else 1},
            "results": [result]
        }
    else:
        # Run full suite
        report = runner.run_all_tests()
    
    # Save report if requested
    if args.save_report:
        with open(args.save_report, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: {args.save_report}")
    
    # Exit with appropriate code
    sys.exit(0 if report["overall_success"] else 1)


if __name__ == "__main__":
    main()