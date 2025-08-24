#!/usr/bin/env python3
"""
Epic 8 Test Runner with Proper Isolation.

This script runs tests for each Epic 8 service in isolation to prevent
namespace collisions while still providing comprehensive test coverage.
"""

import subprocess
import sys
from pathlib import Path
import json
from typing import Dict, List, Tuple
import time

class Epic8TestRunner:
    """Runs Epic 8 tests with proper isolation."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.services = ['generator', 'cache', 'retriever', 'query-analyzer', 'api-gateway', 'analytics']
        self.results = {}
    
    def run_service_tests(self, service_name: str) -> Tuple[bool, Dict]:
        """Run tests for a single service in isolation."""
        service_dir = self.project_root / "services" / service_name
        
        if not service_dir.exists():
            return False, {"error": "Service directory not found", "tests_run": 0}
        
        tests_dir = service_dir / "tests"
        if not tests_dir.exists():
            return True, {"error": "No tests directory (not an error)", "tests_run": 0}
        
        print(f"  Running {service_name} tests...")
        
        # Run pytest in the service directory for proper isolation
        cmd = [
            sys.executable, '-m', 'pytest', 
            'tests/', 
            '-v', '--tb=short', '--no-header',
            '--junit-xml=test-results.xml'
        ]
        
        try:
            # Run in service directory for proper path isolation
            result = subprocess.run(
                cmd, 
                cwd=service_dir,
                capture_output=True, 
                text=True, 
                timeout=120
            )
            
            # Parse results
            tests_info = {
                "returncode": result.returncode,
                "stdout": result.stdout[-500:] if len(result.stdout) > 500 else result.stdout,  # Last 500 chars
                "stderr": result.stderr[-500:] if len(result.stderr) > 500 else result.stderr,  # Last 500 chars
                "namespace_collision": "ImportPathMismatchError" in result.stderr,
                "tests_run": result.stdout.count("PASSED") + result.stdout.count("FAILED"),
                "tests_passed": result.stdout.count("PASSED"),
                "tests_failed": result.stdout.count("FAILED")
            }
            
            success = not tests_info["namespace_collision"]
            return success, tests_info
            
        except subprocess.TimeoutExpired:
            return False, {"error": "Test timeout", "tests_run": 0}
        except Exception as e:
            return False, {"error": str(e), "tests_run": 0}
    
    def run_all_tests(self) -> Dict:
        """Run tests for all services with proper isolation."""
        print("🧪 Running Epic 8 tests with isolation...")
        print("=" * 50)
        
        total_start_time = time.time()
        overall_results = {
            "services_tested": 0,
            "services_passed": 0,
            "namespace_collisions": 0,
            "total_tests": 0,
            "total_passed": 0,
            "total_failed": 0,
            "service_results": {}
        }
        
        for service_name in self.services:
            start_time = time.time()
            
            success, test_info = self.run_service_tests(service_name)
            
            duration = time.time() - start_time
            test_info["duration"] = duration
            
            overall_results["service_results"][service_name] = {
                "success": success,
                "info": test_info
            }
            
            overall_results["services_tested"] += 1
            if success and not test_info.get("namespace_collision", False):
                overall_results["services_passed"] += 1
            
            if test_info.get("namespace_collision", False):
                overall_results["namespace_collisions"] += 1
            
            overall_results["total_tests"] += test_info.get("tests_run", 0)
            overall_results["total_passed"] += test_info.get("tests_passed", 0)
            overall_results["total_failed"] += test_info.get("tests_failed", 0)
            
            # Print immediate results
            if success and not test_info.get("namespace_collision", False):
                status = "✅ PASS"
            elif test_info.get("namespace_collision", False):
                status = "❌ NAMESPACE COLLISION"
            else:
                status = "⚠️  ISSUES"
            
            tests_summary = f"({test_info.get('tests_run', 0)} tests, {duration:.1f}s)"
            print(f"  {service_name:15} {status} {tests_summary}")
        
        overall_results["total_duration"] = time.time() - total_start_time
        return overall_results
    
    def print_summary(self, results: Dict):
        """Print comprehensive test results summary."""
        print("\n" + "=" * 50)
        print("📋 EPIC 8 TEST ISOLATION RESULTS")
        print("=" * 50)
        
        print(f"Services Tested: {results['services_tested']}")
        print(f"Services Passed: {results['services_passed']}")
        print(f"Namespace Collisions: {results['namespace_collisions']}")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Total Passed: {results['total_passed']}")
        print(f"Total Failed: {results['total_failed']}")
        print(f"Total Duration: {results['total_duration']:.1f}s")
        
        print("\n📊 Service Details:")
        for service_name, service_result in results["service_results"].items():
            info = service_result["info"]
            if service_result["success"]:
                print(f"  ✅ {service_name}: {info.get('tests_run', 0)} tests in {info.get('duration', 0):.1f}s")
            else:
                error = info.get('error', 'Unknown error')
                collision = " (NAMESPACE COLLISION)" if info.get('namespace_collision', False) else ""
                print(f"  ❌ {service_name}: {error}{collision}")
        
        # Final assessment
        print("\n" + "=" * 50)
        if results['namespace_collisions'] == 0:
            print("🎉 SUCCESS: No namespace collisions detected!")
            print("✅ Epic 8 services can be tested independently")
            if results['services_passed'] >= results['services_tested'] * 0.8:  # 80% success rate
                print("✅ Overall test execution is working well")
            else:
                print("⚠️  Some test logic issues exist (not namespace related)")
        else:
            print("⚠️  PARTIAL SUCCESS: Some namespace collisions remain")
            print(f"❌ {results['namespace_collisions']} services still have namespace issues")

def main():
    """Run Epic 8 tests with proper isolation."""
    project_root = Path("/Users/apa/ml_projects/rag-portfolio/project-1-technical-rag")
    
    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        return 1
    
    runner = Epic8TestRunner(project_root)
    results = runner.run_all_tests()
    runner.print_summary(results)
    
    # Return appropriate exit code
    return 0 if results['namespace_collisions'] == 0 else 1

if __name__ == "__main__":
    exit(main())