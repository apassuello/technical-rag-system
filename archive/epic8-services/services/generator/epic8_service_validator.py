#!/usr/bin/env python3
"""
Epic 8 Service Validation Script
===============================

Comprehensive validation of all Epic 8 microservices:
- Health endpoint checks
- Service availability testing
- Basic functionality validation
- Import error detection
- Configuration validation
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

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

class ServiceValidator:
    """Validates Epic 8 services comprehensively."""
    
    def __init__(self):
        self.results = {}
        self.project_root = Path(__file__).resolve().parents[2]
        
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
                    print(f"Warning: Health check response is not JSON: {e}", file=sys.stderr)
                    result["details"] = {"raw_response": response.text}
            else:
                result["health_status"] = "unhealthy"
                result["error"] = f"HTTP {response.status_code}"
                try:
                    result["details"] = response.json()
                except (ValueError, json.JSONDecodeError) as e:
                    # Error response is not valid JSON
                    print(f"Warning: Error response is not JSON: {e}", file=sys.stderr)
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
    
    def test_service_endpoints(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test additional endpoints beyond health."""
        endpoints = []
        base_url = config["url"]
        
        # Common endpoints to test
        test_endpoints = [
            "/health/live",
            "/health/ready", 
            "/docs",
            "/metrics"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=3)
                endpoints.append({
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "available": response.status_code < 400
                })
            except requests.RequestException as e:
                # Connection failed, timeout, or other network error
                endpoints.append({
                    "endpoint": endpoint,
                    "status_code": None,
                    "available": False,
                    "error": f"Connection failed: {e}"
                })
                
        return {"endpoints": endpoints}
    
    def check_service_logs(self, service_name: str) -> Dict[str, Any]:
        """Check for obvious errors in service startup."""
        log_info = {
            "import_errors": False,
            "startup_errors": False,
            "warnings": [],
            "status": "unknown"
        }
        
        try:
            # Check if service directory exists and has proper structure
            service_dir = self.project_root / "services" / service_name
            if not service_dir.exists():
                log_info["startup_errors"] = True
                log_info["warnings"].append(f"Service directory {service_dir} not found")
                return log_info
            
            # Check for main.py
            main_py = service_dir / "app" / "main.py"
            if not main_py.exists():
                log_info["startup_errors"] = True
                log_info["warnings"].append(f"main.py not found at {main_py}")
                return log_info
                
            log_info["status"] = "structure_ok"
            
        except Exception as e:
            log_info["startup_errors"] = True
            log_info["warnings"].append(f"Error checking service structure: {e}")
            
        return log_info
    
    def validate_service_imports(self, service_name: str) -> Dict[str, Any]:
        """Test if service can be imported without errors."""
        import_result = {
            "can_import": False,
            "import_time": None,
            "error": None,
            "warnings": []
        }
        
        try:
            service_dir = self.project_root / "services" / service_name
            if not service_dir.exists():
                import_result["error"] = f"Service directory not found: {service_dir}"
                return import_result
            
            # Try to import the service
            start_time = time.time()
            
            import_cmd = [
                sys.executable, "-c",
                f"""
import sys
sys.path.insert(0, '{self.project_root}')
sys.path.insert(0, '{service_dir}')
try:
    from generator_app.main import app
    print('IMPORT_SUCCESS')
except Exception as e:
    print(f'IMPORT_ERROR: {{e}}')
    import traceback
    traceback.print_exc()
"""
            ]
            
            result = subprocess.run(
                import_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=service_dir
            )
            
            import_time = time.time() - start_time
            import_result["import_time"] = round(import_time * 1000, 2)  # ms
            
            if "IMPORT_SUCCESS" in result.stdout:
                import_result["can_import"] = True
            else:
                import_result["can_import"] = False
                import_result["error"] = result.stdout + result.stderr
                
        except subprocess.TimeoutExpired:
            import_result["error"] = "Import test timeout"
        except Exception as e:
            import_result["error"] = str(e)
            
        return import_result
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("🔍 Starting Epic 8 Service Validation")
        print("=" * 50)
        
        validation_results = {
            "timestamp": time.time(),
            "summary": {
                "total_services": len(SERVICES),
                "healthy_services": 0,
                "unhealthy_services": 0,
                "not_running_services": 0,
                "import_errors": 0
            },
            "services": {}
        }
        
        for service_name, config in SERVICES.items():
            print(f"\n🔧 Validating {service_name}...")
            
            service_result = {
                "health": self.check_service_health(service_name, config),
                "endpoints": self.test_service_endpoints(service_name, config),
                "logs": self.check_service_logs(service_name),
                "imports": self.validate_service_imports(service_name)
            }
            
            validation_results["services"][service_name] = service_result
            
            # Update summary
            health_status = service_result["health"]["health_status"]
            if health_status == "healthy":
                validation_results["summary"]["healthy_services"] += 1
                print(f"   ✅ {service_name}: HEALTHY")
            elif health_status == "not_running":
                validation_results["summary"]["not_running_services"] += 1
                print(f"   ❌ {service_name}: NOT RUNNING")
            else:
                validation_results["summary"]["unhealthy_services"] += 1
                print(f"   ⚠️  {service_name}: UNHEALTHY - {service_result['health'].get('error', 'Unknown error')}")
            
            if not service_result["imports"]["can_import"]:
                validation_results["summary"]["import_errors"] += 1
                print(f"   ❌ {service_name}: IMPORT ERROR")
        
        return validation_results
    
    def print_detailed_report(self, results: Dict[str, Any]):
        """Print detailed validation report."""
        print("\n" + "=" * 60)
        print("📊 DETAILED VALIDATION REPORT")
        print("=" * 60)
        
        summary = results["summary"]
        print("\n📈 SUMMARY:")
        print(f"   Total Services: {summary['total_services']}")
        print(f"   ✅ Healthy: {summary['healthy_services']}")
        print(f"   ⚠️  Unhealthy: {summary['unhealthy_services']}")
        print(f"   ❌ Not Running: {summary['not_running_services']}")
        print(f"   🚫 Import Errors: {summary['import_errors']}")
        
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
            
            # Import status
            imports = service_data["imports"]
            import_emoji = "✅" if imports["can_import"] else "❌"
            print(f"   {import_emoji} Import: {'Success' if imports['can_import'] else 'Failed'}")
            
            if imports["import_time"]:
                print(f"   ⏱️  Import Time: {imports['import_time']}ms")
            
            # Endpoints
            endpoints = service_data["endpoints"]["endpoints"]
            available_endpoints = [ep for ep in endpoints if ep["available"]]
            print(f"   🔗 Endpoints: {len(available_endpoints)}/{len(endpoints)} available")
            
            # Service details (if available)
            if health.get("details") and isinstance(health["details"], dict):
                if "generator_initialized" in health["details"]:
                    init_status = health["details"]["generator_initialized"]
                    print(f"   🏗️  Initialized: {'Yes' if init_status else 'No'}")
                if "components_loaded" in health["details"]:
                    comp_status = health["details"]["components_loaded"]
                    print(f"   🔧 Components: {'Loaded' if comp_status else 'Failed'}")
        
        print(f"\n⏰ Report generated at: {time.ctime(results['timestamp'])}")

def main():
    validator = ServiceValidator()
    results = validator.run_comprehensive_validation()
    validator.print_detailed_report(results)
    
    # Save results to file
    output_file = "epic8_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Exit with appropriate code
    summary = results["summary"]
    if summary["healthy_services"] == summary["total_services"]:
        print("\n🎉 ALL SERVICES HEALTHY!")
        return 0
    else:
        print("\n⚠️  SOME SERVICES NEED ATTENTION")
        return 1

if __name__ == "__main__":
    sys.exit(main())
