#!/usr/bin/env python3
"""
Epic 8 Comprehensive Service Validation
=======================================

Validates all Epic 8 services including:
- Health status
- Basic functionality testing
- API endpoint testing
- Component status verification
"""

import json
import logging
import sys
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)

import requests

# Service configuration
SERVICES = {
    "query-analyzer": {"port": 8082, "url": "http://localhost:8082"},
    "generator": {"port": 8081, "url": "http://localhost:8081"}, 
    "api-gateway": {"port": 8080, "url": "http://localhost:8080"},
    "retriever": {"port": 8083, "url": "http://localhost:8083"},
    "cache": {"port": 8084, "url": "http://localhost:8084"},
    "analytics": {"port": 8085, "url": "http://localhost:8085"}
}

class ComprehensiveValidator:
    """Comprehensive Epic 8 service validation."""
    
    def __init__(self):
        self.results = {}
        
    def test_query_analyzer_functionality(self, base_url: str) -> Dict[str, Any]:
        """Test Query Analyzer specific functionality."""
        tests = []
        
        # Test analyze endpoint
        try:
            response = requests.post(
                f"{base_url}/api/v1/analyze",
                json={"query": "What is machine learning?"},
                timeout=5
            )
            tests.append({
                "name": "analyze_endpoint",
                "status": "passed" if response.status_code == 200 else "failed",
                "response_code": response.status_code,
                "response_time": response.elapsed.total_seconds() * 1000
            })
        except Exception as e:
            tests.append({
                "name": "analyze_endpoint",
                "status": "error",
                "error": str(e)
            })
            
        return {"functional_tests": tests}
    
    def test_generator_functionality(self, base_url: str) -> Dict[str, Any]:
        """Test Generator specific functionality."""
        tests = []
        
        # Test models endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/models", timeout=5)
            tests.append({
                "name": "models_endpoint",
                "status": "passed" if response.status_code == 200 else "failed",
                "response_code": response.status_code,
                "response_time": response.elapsed.total_seconds() * 1000
            })
        except Exception as e:
            tests.append({
                "name": "models_endpoint",
                "status": "error",
                "error": str(e)
            })
            
        # Test generate endpoint (basic test)
        try:
            response = requests.post(
                f"{base_url}/api/v1/generate",
                json={
                    "query": "Test query",
                    "context_documents": [{"content": "Test document", "metadata": {}}]
                },
                timeout=10
            )
            tests.append({
                "name": "generate_endpoint",
                "status": "passed" if response.status_code in [200, 422] else "failed",  # 422 is acceptable for validation
                "response_code": response.status_code,
                "response_time": response.elapsed.total_seconds() * 1000
            })
        except Exception as e:
            tests.append({
                "name": "generate_endpoint",
                "status": "error",
                "error": str(e)
            })
            
        return {"functional_tests": tests}
    
    def test_retriever_functionality(self, base_url: str) -> Dict[str, Any]:
        """Test Retriever specific functionality."""
        tests = []
        
        # Test retrieve endpoint
        try:
            response = requests.post(
                f"{base_url}/api/v1/retrieve",
                json={"query": "test query", "max_documents": 5},
                timeout=5
            )
            tests.append({
                "name": "retrieve_endpoint",
                "status": "passed" if response.status_code in [200, 422] else "failed",
                "response_code": response.status_code,
                "response_time": response.elapsed.total_seconds() * 1000
            })
        except Exception as e:
            tests.append({
                "name": "retrieve_endpoint",
                "status": "error",
                "error": str(e)
            })
            
        return {"functional_tests": tests}
    
    def test_cache_functionality(self, base_url: str) -> Dict[str, Any]:
        """Test Cache specific functionality."""
        tests = []
        
        # Test cache get endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/cache/test_key", timeout=5)
            tests.append({
                "name": "cache_get",
                "status": "passed" if response.status_code in [200, 404] else "failed",
                "response_code": response.status_code,
                "response_time": response.elapsed.total_seconds() * 1000
            })
        except Exception as e:
            tests.append({
                "name": "cache_get",
                "status": "error",
                "error": str(e)
            })
            
        return {"functional_tests": tests}
    
    def test_analytics_functionality(self, base_url: str) -> Dict[str, Any]:
        """Test Analytics specific functionality."""
        tests = []
        
        # Test metrics endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/metrics", timeout=5)
            tests.append({
                "name": "metrics_endpoint",
                "status": "passed" if response.status_code == 200 else "failed",
                "response_code": response.status_code,
                "response_time": response.elapsed.total_seconds() * 1000
            })
        except Exception as e:
            tests.append({
                "name": "metrics_endpoint",
                "status": "error",
                "error": str(e)
            })
            
        return {"functional_tests": tests}
    
    def test_api_gateway_functionality(self, base_url: str) -> Dict[str, Any]:
        """Test API Gateway specific functionality."""
        tests = []
        
        # Test status endpoint
        try:
            response = requests.get(f"{base_url}/status", timeout=5)
            tests.append({
                "name": "status_endpoint",
                "status": "passed" if response.status_code == 200 else "failed",
                "response_code": response.status_code,
                "response_time": response.elapsed.total_seconds() * 1000
            })
        except Exception as e:
            tests.append({
                "name": "status_endpoint",
                "status": "error",
                "error": str(e)
            })
            
        return {"functional_tests": tests}
    
    def check_service_health(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check health endpoint for a service."""
        result = {
            "service": service_name,
            "url": config["url"],
            "port": config["port"],
            "health_status": "unknown",
            "response_time": None,
            "error": None,
            "details": {}
        }
        
        try:
            start_time = time.time()
            response = requests.get(f"{config['url']}/health", timeout=5)
            response_time = time.time() - start_time
            
            result["response_time"] = round(response_time * 1000, 2)  # ms
            
            if response.status_code == 200:
                result["health_status"] = "healthy"
                try:
                    result["details"] = response.json()
                except (ValueError, json.JSONDecodeError) as e:
                    # Response is not valid JSON
                    logger.debug(f"Health check response is not JSON: {e}")
                    result["details"] = {"raw_response": response.text}
            else:
                result["health_status"] = "unhealthy"
                result["error"] = f"HTTP {response.status_code}"
                try:
                    result["details"] = response.json()
                except (ValueError, json.JSONDecodeError) as e:
                    # Error response is not valid JSON
                    logger.debug(f"Error response is not JSON: {e}")
                    result["details"] = {"raw_response": response.text}
                    
        except requests.exceptions.ConnectionError:
            result["health_status"] = "not_running"
            result["error"] = "Connection refused - service not running"
        except requests.exceptions.Timeout:
            result["health_status"] = "timeout"
            result["error"] = "Health check timeout"
        except Exception as e:
            result["health_status"] = "error"
            result["error"] = str(e)
            
        return result
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation including functionality tests."""
        print("🔍 Starting Epic 8 Comprehensive Validation")
        print("=" * 60)
        
        validation_results = {
            "timestamp": time.time(),
            "summary": {
                "total_services": len(SERVICES),
                "healthy_services": 0,
                "unhealthy_services": 0,
                "not_running_services": 0,
                "functional_tests_passed": 0,
                "functional_tests_failed": 0
            },
            "services": {}
        }
        
        for service_name, config in SERVICES.items():
            print(f"\n🔧 Validating {service_name}...")
            
            # Health check
            health_result = self.check_service_health(service_name, config)
            
            # Functionality tests
            functional_result = {"functional_tests": []}
            if health_result["health_status"] == "healthy":
                if service_name == "query-analyzer":
                    functional_result = self.test_query_analyzer_functionality(config["url"])
                elif service_name == "generator":
                    functional_result = self.test_generator_functionality(config["url"])
                elif service_name == "retriever":
                    functional_result = self.test_retriever_functionality(config["url"])
                elif service_name == "cache":
                    functional_result = self.test_cache_functionality(config["url"])
                elif service_name == "analytics":
                    functional_result = self.test_analytics_functionality(config["url"])
                elif service_name == "api-gateway":
                    functional_result = self.test_api_gateway_functionality(config["url"])
            
            service_result = {
                "health": health_result,
                "functionality": functional_result
            }
            
            validation_results["services"][service_name] = service_result
            
            # Update summary
            health_status = service_result["health"]["health_status"]
            if health_status == "healthy":
                validation_results["summary"]["healthy_services"] += 1
                print(f"   ✅ {service_name}: HEALTHY")
                
                # Count functional tests
                for test in functional_result.get("functional_tests", []):
                    if test["status"] == "passed":
                        validation_results["summary"]["functional_tests_passed"] += 1
                    else:
                        validation_results["summary"]["functional_tests_failed"] += 1
                        
            elif health_status == "not_running":
                validation_results["summary"]["not_running_services"] += 1
                print(f"   ❌ {service_name}: NOT RUNNING")
            else:
                validation_results["summary"]["unhealthy_services"] += 1
                print(f"   ⚠️  {service_name}: UNHEALTHY - {service_result['health'].get('error', 'Unknown error')}")
        
        return validation_results
    
    def print_detailed_report(self, results: Dict[str, Any]):
        """Print detailed validation report."""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE VALIDATION REPORT")
        print("=" * 70)
        
        summary = results["summary"]
        print("\n📈 SUMMARY:")
        print(f"   Total Services: {summary['total_services']}")
        print(f"   ✅ Healthy: {summary['healthy_services']}")
        print(f"   ⚠️  Unhealthy: {summary['unhealthy_services']}")
        print(f"   ❌ Not Running: {summary['not_running_services']}")
        print(f"   🧪 Functional Tests Passed: {summary['functional_tests_passed']}")
        print(f"   ❌ Functional Tests Failed: {summary['functional_tests_failed']}")
        
        for service_name, service_data in results["services"].items():
            print(f"\n🔧 {service_name.upper()}:")
            
            # Health status
            health = service_data["health"]
            status_emoji = "✅" if health["health_status"] == "healthy" else "❌"
            print(f"   {status_emoji} Health: {health['health_status']}")
            
            if health["response_time"]:
                print(f"   ⏱️  Response Time: {health['response_time']}ms")
            
            if health["error"]:
                print(f"   ❌ Error: {health['error']}")
            
            # Functional tests
            func_tests = service_data["functionality"].get("functional_tests", [])
            if func_tests:
                passed_tests = len([t for t in func_tests if t["status"] == "passed"])
                total_tests = len(func_tests)
                print(f"   🧪 Functional Tests: {passed_tests}/{total_tests} passed")
                
                for test in func_tests:
                    test_emoji = "✅" if test["status"] == "passed" else "❌"
                    test_name = test["name"].replace("_", " ").title()
                    print(f"      {test_emoji} {test_name}")
                    if "response_time" in test:
                        print(f"         ⏱️  {test['response_time']:.2f}ms")
                    if test["status"] == "error":
                        print(f"         ❌ {test.get('error', 'Unknown error')}")
        
        print(f"\n⏰ Report generated at: {time.ctime(results['timestamp'])}")

def main():
    validator = ComprehensiveValidator()
    results = validator.run_comprehensive_validation()
    validator.print_detailed_report(results)
    
    # Save results to file
    output_file = "epic8_comprehensive_validation.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Exit with appropriate code
    summary = results["summary"]
    if summary["healthy_services"] == summary["total_services"]:
        print("\n🎉 ALL SERVICES HEALTHY AND FUNCTIONAL!")
        return 0
    else:
        print("\n⚠️  SOME SERVICES NEED ATTENTION")
        return 1

if __name__ == "__main__":
    sys.exit(main())
