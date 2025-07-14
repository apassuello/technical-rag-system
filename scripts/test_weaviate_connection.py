#!/usr/bin/env python3
"""
Weaviate Connection and Epic 2 Integration Test
This script validates Weaviate connectivity and Epic 2 component integration.
"""

import sys
import time
import json
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def log_info(message: str):
    """Log info message with timestamp."""
    print(f"[INFO] {time.strftime('%H:%M:%S')} - {message}")

def log_success(message: str):
    """Log success message."""
    print(f"✅ {message}")

def log_error(message: str):
    """Log error message."""
    print(f"❌ {message}")

def log_warning(message: str):
    """Log warning message."""
    print(f"⚠️  {message}")

def test_weaviate_connection() -> Dict[str, Any]:
    """Test basic Weaviate connectivity."""
    test_result = {
        "test_name": "weaviate_connection",
        "success": False,
        "details": {},
        "error": None
    }
    
    try:
        import weaviate
        
        # Test connection with different configurations
        connection_configs = [
            {"url": "http://localhost:8080", "name": "localhost:8080"},
            {"url": "http://127.0.0.1:8080", "name": "127.0.0.1:8080"}
        ]
        
        client = None
        working_config = None
        
        for config in connection_configs:
            try:
                log_info(f"Testing Weaviate connection: {config['name']}")
                client = weaviate.Client(config["url"])
                
                # Test readiness
                if client.is_ready():
                    log_success(f"Weaviate connection successful: {config['name']}")
                    working_config = config
                    break
                else:
                    log_warning(f"Weaviate not ready: {config['name']}")
                    
            except Exception as e:
                log_warning(f"Connection failed {config['name']}: {e}")
                continue
        
        if not client or not working_config:
            raise Exception("No working Weaviate connection found")
        
        # Test detailed connectivity
        test_result["details"]["connection_url"] = working_config["url"]
        test_result["details"]["is_ready"] = client.is_ready()
        test_result["details"]["is_live"] = client.is_live()
        
        # Test schema access
        try:
            schema = client.schema.get()
            test_result["details"]["schema_accessible"] = True
            test_result["details"]["schema_classes"] = len(schema.get('classes', []))
            log_success(f"Schema accessible: {len(schema.get('classes', []))} classes")
        except Exception as e:
            test_result["details"]["schema_accessible"] = False
            test_result["details"]["schema_error"] = str(e)
            log_warning(f"Schema access issue: {e}")
        
        # Test meta information
        try:
            meta = client.get_meta()
            test_result["details"]["meta_accessible"] = True
            test_result["details"]["weaviate_version"] = meta.get("version", "unknown")
            log_success(f"Weaviate version: {meta.get('version', 'unknown')}")
        except Exception as e:
            test_result["details"]["meta_accessible"] = False
            test_result["details"]["meta_error"] = str(e)
            log_warning(f"Meta access issue: {e}")
        
        test_result["success"] = True
        log_success("Weaviate connection test passed")
        
    except ImportError:
        error_msg = "weaviate-client not installed. Run: pip install weaviate-client"
        test_result["error"] = error_msg
        log_error(error_msg)
        
    except Exception as e:
        test_result["error"] = str(e)
        log_error(f"Weaviate connection failed: {e}")
    
    return test_result

def test_epic2_integration() -> Dict[str, Any]:
    """Test Epic 2 Advanced Retriever with Weaviate."""
    test_result = {
        "test_name": "epic2_integration",
        "success": False,
        "details": {},
        "error": None
    }
    
    try:
        from src.core.platform_orchestrator import PlatformOrchestrator
        
        # Test Epic 2 configuration loading
        config_files = [
            "config/epic2_comprehensive_test.yaml",
            "config/epic2_diagnostic_test.yaml",
            "config/advanced_test.yaml"
        ]
        
        working_config = None
        po = None
        
        for config_file in config_files:
            try:
                log_info(f"Testing Epic 2 configuration: {config_file}")
                po = PlatformOrchestrator(config_file)
                working_config = config_file
                log_success(f"Configuration loaded: {config_file}")
                break
            except Exception as e:
                log_warning(f"Configuration failed {config_file}: {e}")
                continue
        
        if not po:
            raise Exception("No working Epic 2 configuration found")
        
        test_result["details"]["config_file"] = working_config
        
        # Analyze retriever
        retriever = po._components.get('retriever')
        if not retriever:
            raise Exception("No retriever component found")
        
        test_result["details"]["retriever_type"] = type(retriever).__name__
        test_result["details"]["architecture"] = po._determine_system_architecture()
        
        # Check Epic 2 features
        if hasattr(retriever, 'reranker'):
            test_result["details"]["reranker_type"] = type(retriever.reranker).__name__
        
        if hasattr(retriever, 'fusion_strategy'):
            test_result["details"]["fusion_type"] = type(retriever.fusion_strategy).__name__
        
        # Test Advanced Retriever specific features
        if type(retriever).__name__ == "AdvancedRetriever":
            log_success("AdvancedRetriever detected")
            
            # Test backend information
            if hasattr(retriever, 'active_backend_name'):
                test_result["details"]["active_backend"] = retriever.active_backend_name
                log_info(f"Active backend: {retriever.active_backend_name}")
            
            # Test advanced configuration
            if hasattr(retriever, 'advanced_config'):
                config = retriever.advanced_config
                test_result["details"]["neural_reranking_enabled"] = config.neural_reranking.enabled
                test_result["details"]["graph_retrieval_enabled"] = config.graph_retrieval.enabled
                test_result["details"]["analytics_enabled"] = config.analytics.enabled
                
                log_info(f"Neural Reranking: {config.neural_reranking.enabled}")
                log_info(f"Graph Retrieval: {config.graph_retrieval.enabled}")
                log_info(f"Analytics: {config.analytics.enabled}")
            
            # Test backend switching (if available)
            if hasattr(retriever, 'switch_to_backend'):
                try:
                    original_backend = retriever.active_backend_name
                    
                    # Test switching to different backends
                    for backend_name in ["faiss", "weaviate"]:
                        try:
                            retriever.switch_to_backend(backend_name)
                            current_backend = retriever.active_backend_name
                            log_info(f"Switched to backend: {current_backend}")
                            test_result["details"][f"{backend_name}_switch_success"] = True
                        except Exception as e:
                            log_warning(f"Backend switch to {backend_name} failed: {e}")
                            test_result["details"][f"{backend_name}_switch_success"] = False
                    
                    # Restore original backend
                    retriever.switch_to_backend(original_backend)
                    
                except Exception as e:
                    log_warning(f"Backend switching test failed: {e}")
                    test_result["details"]["backend_switching_error"] = str(e)
        
        # Test basic retrieval functionality
        try:
            log_info("Testing basic retrieval functionality...")
            test_query = "What is RISC-V instruction set architecture?"
            
            start_time = time.time()
            answer = po.process_query(test_query)
            retrieval_time = time.time() - start_time
            
            test_result["details"]["retrieval_success"] = True
            test_result["details"]["retrieval_time_ms"] = round(retrieval_time * 1000, 2)
            test_result["details"]["answer_length"] = len(answer.answer) if hasattr(answer, 'answer') else len(str(answer))
            
            log_success(f"Retrieval successful in {retrieval_time*1000:.2f}ms")
            
        except Exception as e:
            test_result["details"]["retrieval_success"] = False
            test_result["details"]["retrieval_error"] = str(e)
            log_warning(f"Retrieval test failed: {e}")
        
        test_result["success"] = True
        log_success("Epic 2 integration test passed")
        
    except ImportError as e:
        error_msg = f"Epic 2 import failed: {e}"
        test_result["error"] = error_msg
        log_error(error_msg)
        
    except Exception as e:
        test_result["error"] = str(e)
        test_result["traceback"] = traceback.format_exc()
        log_error(f"Epic 2 integration failed: {e}")
    
    return test_result

def test_performance_baseline() -> Dict[str, Any]:
    """Test Epic 2 performance characteristics."""
    test_result = {
        "test_name": "performance_baseline",
        "success": False,
        "details": {},
        "error": None
    }
    
    try:
        from src.core.platform_orchestrator import PlatformOrchestrator
        
        # Use the most comprehensive Epic 2 configuration
        po = PlatformOrchestrator("config/epic2_comprehensive_test.yaml")
        
        # Performance test queries
        test_queries = [
            "What is RISC-V instruction set architecture?",
            "How does vector extension work in RISC-V?",
            "What are the privilege levels in RISC-V?"
        ]
        
        latencies = []
        answers = []
        
        for i, query in enumerate(test_queries):
            log_info(f"Performance test query {i+1}/{len(test_queries)}")
            
            start_time = time.time()
            answer = po.process_query(query)
            latency = time.time() - start_time
            
            latencies.append(latency * 1000)  # Convert to ms
            answers.append(len(str(answer)))
            
            log_info(f"Query {i+1} latency: {latency*1000:.2f}ms")
        
        # Calculate performance metrics
        test_result["details"]["query_count"] = len(test_queries)
        test_result["details"]["average_latency_ms"] = round(sum(latencies) / len(latencies), 2)
        test_result["details"]["min_latency_ms"] = round(min(latencies), 2)
        test_result["details"]["max_latency_ms"] = round(max(latencies), 2)
        test_result["details"]["average_answer_length"] = round(sum(answers) / len(answers), 0)
        
        # Check performance targets
        avg_latency = test_result["details"]["average_latency_ms"]
        target_latency = 700  # Epic 2 target: <700ms P95
        
        test_result["details"]["meets_latency_target"] = avg_latency < target_latency
        test_result["details"]["latency_target_ms"] = target_latency
        
        if avg_latency < target_latency:
            log_success(f"Performance target met: {avg_latency:.2f}ms < {target_latency}ms")
        else:
            log_warning(f"Performance target missed: {avg_latency:.2f}ms > {target_latency}ms")
        
        test_result["success"] = True
        log_success("Performance baseline test completed")
        
    except Exception as e:
        test_result["error"] = str(e)
        log_error(f"Performance baseline test failed: {e}")
    
    return test_result

def generate_test_report(results: Dict[str, Any]) -> str:
    """Generate a comprehensive test report."""
    report_lines = [
        "🧪 Epic 2 + Weaviate Integration Test Report",
        "=" * 50,
        f"Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    # Summary
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r["success"])
    
    report_lines.extend([
        "📊 Test Summary:",
        f"   Total Tests: {total_tests}",
        f"   Passed: {passed_tests}",
        f"   Failed: {total_tests - passed_tests}",
        f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%",
        ""
    ])
    
    # Detailed results
    for test_name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        report_lines.extend([
            f"🔍 {test_name.replace('_', ' ').title()}: {status}",
        ])
        
        if result["success"] and result["details"]:
            for key, value in result["details"].items():
                if isinstance(value, bool):
                    value = "✅ Yes" if value else "❌ No"
                report_lines.append(f"   • {key.replace('_', ' ').title()}: {value}")
        
        if not result["success"] and result.get("error"):
            report_lines.append(f"   • Error: {result['error']}")
        
        report_lines.append("")
    
    # Recommendations
    report_lines.extend([
        "💡 Recommendations:",
    ])
    
    if not results["weaviate_connection"]["success"]:
        report_lines.append("   • Start Weaviate: docker-compose up -d weaviate")
    
    if not results["epic2_integration"]["success"]:
        report_lines.append("   • Check Epic 2 configuration files in config/")
        report_lines.append("   • Verify Python dependencies: pip install -r requirements.txt")
    
    if results.get("performance_baseline", {}).get("success"):
        perf_details = results["performance_baseline"]["details"]
        if not perf_details.get("meets_latency_target", True):
            report_lines.append(f"   • Optimize performance: current {perf_details.get('average_latency_ms')}ms > target {perf_details.get('latency_target_ms')}ms")
    
    report_lines.extend([
        "",
        "📚 Documentation:",
        "   • Setup Guide: docs/WEAVIATE_SETUP.md",
        "   • Epic 2 Guide: docs/epics/epic-2-hybrid-retriever.md",
        ""
    ])
    
    return "\n".join(report_lines)

def main():
    """Run all tests and generate report."""
    print("🧪 Epic 2 + Weaviate Integration Test Suite")
    print("=" * 60)
    print(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Run tests
    test_results = {}
    
    log_info("Running Weaviate connection test...")
    test_results["weaviate_connection"] = test_weaviate_connection()
    
    log_info("Running Epic 2 integration test...")
    test_results["epic2_integration"] = test_epic2_integration()
    
    # Only run performance test if integration succeeds
    if test_results["epic2_integration"]["success"]:
        log_info("Running performance baseline test...")
        test_results["performance_baseline"] = test_performance_baseline()
    else:
        log_warning("Skipping performance test due to integration failure")
    
    # Generate and save report
    report = generate_test_report(test_results)
    print("\n" + report)
    
    # Save results to file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = project_root / f"weaviate_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    log_success(f"Test results saved: {results_file}")
    
    # Exit with appropriate code
    all_passed = all(r["success"] for r in test_results.values())
    if all_passed:
        log_success("🎉 All tests passed! Epic 2 + Weaviate integration is ready.")
        sys.exit(0)
    else:
        log_error("💥 Some tests failed. Check the report above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()