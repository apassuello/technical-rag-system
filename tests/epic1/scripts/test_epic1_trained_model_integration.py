#!/usr/bin/env python3
"""
Epic 1 Trained Model Integration Test - End-to-End Validation.

This script validates that our trained PyTorch models integrate seamlessly
with the existing Epic 1 infrastructure, testing the complete bridge
architecture from trained models through to final query processing.

Key Test Areas:
1. EpicMLAdapter initialization and configuration
2. Trained model loading and availability
3. End-to-end query analysis with trained models
4. Fallback to Epic 1 infrastructure when needed
5. Performance comparison between trained models and fallback
6. Integration with existing ComponentFactory and configuration system
"""

import os
import sys
import asyncio
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.core.component_factory import ComponentFactory
from src.components.query_processors.analyzers.epic_ml_adapter import EpicMLAdapter
from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer
from src.utils.config import load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Epic1IntegrationTester:
    """
    Comprehensive integration tester for Epic 1 trained models with existing system.
    """
    
    def __init__(self):
        """Initialize the integration tester."""
        self.factory = ComponentFactory()
        self.config_dir = Path("config")
        self.model_dir = Path("models/epic1")
        self.test_queries = [
            "What is cache memory?",
            "How do I implement proper logging and monitoring for a Python Flask application in production?", 
            "What optimization techniques minimize energy consumption in datacenters while maintaining quality of service guarantees and handling dynamic workload variations across heterogeneous hardware?",
            "How do distributed hash tables maintain routing table consistency while handling concurrent updates?",
            "What are the theoretical foundations for proving safety and liveness properties of distributed consensus algorithms?"
        ]
        self.results = {}
        
        logger.info("Epic1IntegrationTester initialized")
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        Run comprehensive integration test covering all aspects.
        
        Returns:
            Test results summary
        """
        logger.info("🚀 Starting Epic 1 comprehensive integration test")
        start_time = time.time()
        
        try:
            # Test 1: Component factory integration
            test1_results = await self._test_component_factory_integration()
            
            # Test 2: EpicMLAdapter initialization
            test2_results = await self._test_epic_ml_adapter_initialization()
            
            # Test 3: Trained model availability
            test3_results = await self._test_trained_model_availability()
            
            # Test 4: End-to-end query analysis
            test4_results = await self._test_end_to_end_analysis()
            
            # Test 5: Performance comparison
            test5_results = await self._test_performance_comparison()
            
            # Test 6: Fallback mechanism
            test6_results = await self._test_fallback_mechanism()
            
            # Test 7: Configuration integration
            test7_results = await self._test_configuration_integration()
            
            total_time = time.time() - start_time
            
            # Compile comprehensive results
            self.results = {
                "test_info": {
                    "timestamp": time.strftime("%Y%m%d_%H%M%S"),
                    "total_test_time_seconds": total_time,
                    "test_queries_count": len(self.test_queries)
                },
                "test_results": {
                    "component_factory_integration": test1_results,
                    "epic_ml_adapter_initialization": test2_results,
                    "trained_model_availability": test3_results,
                    "end_to_end_analysis": test4_results,
                    "performance_comparison": test5_results,
                    "fallback_mechanism": test6_results,
                    "configuration_integration": test7_results
                },
                "overall_summary": self._generate_summary()
            }
            
            logger.info(f"✅ Epic 1 comprehensive integration test completed in {total_time:.2f}s")
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Integration test failed: {e}")
            self.results = {
                "error": str(e),
                "test_failed": True,
                "timestamp": time.strftime("%Y%m%d_%H%M%S")
            }
            return self.results
    
    async def _test_component_factory_integration(self) -> Dict[str, Any]:
        """Test Epic ML Adapter integration with ComponentFactory."""
        logger.info("🧪 Testing ComponentFactory integration...")
        
        try:
            # Test analyzer creation through factory
            analyzer = self.factory.create_analyzer("epic1_ml_adapter")
            
            success = analyzer is not None and isinstance(analyzer, EpicMLAdapter)
            
            return {
                "test_name": "Component Factory Integration",
                "success": success,
                "analyzer_type": type(analyzer).__name__,
                "is_epic_ml_adapter": isinstance(analyzer, EpicMLAdapter),
                "factory_mapping_exists": "epic1_ml_adapter" in self.factory._QUERY_ANALYZERS
            }
            
        except Exception as e:
            return {
                "test_name": "Component Factory Integration", 
                "success": False,
                "error": str(e)
            }
    
    async def _test_epic_ml_adapter_initialization(self) -> Dict[str, Any]:
        """Test EpicMLAdapter initialization and configuration."""
        logger.info("🧪 Testing EpicMLAdapter initialization...")
        
        try:
            # Initialize with default config
            adapter = EpicMLAdapter()
            
            # Test basic properties
            has_trained_system = hasattr(adapter, 'trained_system') and adapter.trained_system is not None
            models_available = adapter.is_trained_models_available()
            has_original_views = hasattr(adapter, 'original_views') and len(adapter.original_views) > 0
            has_view_adapters = hasattr(adapter, 'views') and len(adapter.views) > 0
            
            # Test view adapter types
            view_adapter_info = {}
            if hasattr(adapter, 'views'):
                for view_name, view in adapter.views.items():
                    view_adapter_info[view_name] = type(view).__name__
            
            return {
                "test_name": "EpicMLAdapter Initialization",
                "success": True,
                "has_trained_system": has_trained_system,
                "models_available": models_available,
                "has_original_views": has_original_views,
                "has_view_adapters": has_view_adapters,
                "view_count": len(adapter.views) if hasattr(adapter, 'views') else 0,
                "view_adapter_types": view_adapter_info,
                "model_info": adapter.get_trained_model_info()
            }
            
        except Exception as e:
            return {
                "test_name": "EpicMLAdapter Initialization",
                "success": False,
                "error": str(e)
            }
    
    async def _test_trained_model_availability(self) -> Dict[str, Any]:
        """Test trained model loading and availability."""
        logger.info("🧪 Testing trained model availability...")
        
        try:
            adapter = EpicMLAdapter(model_dir=str(self.model_dir))
            
            # Check model files
            model_files_exist = self._check_model_files()
            
            # Test model system availability
            trained_system_available = adapter.trained_system and adapter.trained_system.is_available()
            
            # Get detailed model info
            model_info = adapter.get_trained_model_info()
            
            # Test individual components
            component_status = {}
            if adapter.trained_system:
                component_status = {
                    "model_adapter_available": adapter.trained_system.model_adapter.is_available(),
                    "views_initialized": len(adapter.trained_system.views) == 5,
                    "predictor_loaded": adapter.trained_system.model_adapter.predictor is not None
                }
            
            return {
                "test_name": "Trained Model Availability",
                "success": trained_system_available,
                "model_files_exist": model_files_exist,
                "trained_system_available": trained_system_available,
                "model_info": model_info,
                "component_status": component_status,
                "model_directory": str(self.model_dir),
                "model_directory_exists": self.model_dir.exists()
            }
            
        except Exception as e:
            return {
                "test_name": "Trained Model Availability",
                "success": False,
                "error": str(e),
                "model_directory": str(self.model_dir),
                "model_directory_exists": self.model_dir.exists()
            }
    
    async def _test_end_to_end_analysis(self) -> Dict[str, Any]:
        """Test end-to-end query analysis with trained models."""
        logger.info("🧪 Testing end-to-end analysis...")
        
        try:
            adapter = EpicMLAdapter(model_dir=str(self.model_dir))
            
            analysis_results = []
            total_analysis_time = 0.0
            successful_analyses = 0
            
            for i, query in enumerate(self.test_queries):
                try:
                    start_time = time.time()
                    result = await adapter.analyze(query, mode='hybrid')
                    analysis_time = time.time() - start_time
                    
                    analysis_results.append({
                        "query_index": i,
                        "query": query[:50] + "..." if len(query) > 50 else query,
                        "complexity_score": result.complexity_score,
                        "complexity_level": result.complexity_level.value if hasattr(result.complexity_level, 'value') else str(result.complexity_level),
                        "confidence": result.confidence,
                        "analysis_time_ms": analysis_time * 1000,
                        "trained_models_used": result.metadata.get('trained_models_used', False),
                        "view_count": len(result.view_results),
                        "successful_views": len([v for v in result.view_results.values() if v.confidence > 0])
                    })
                    
                    total_analysis_time += analysis_time
                    successful_analyses += 1
                    
                except Exception as e:
                    analysis_results.append({
                        "query_index": i,
                        "query": query[:50] + "..." if len(query) > 50 else query,
                        "error": str(e),
                        "failed": True
                    })
            
            avg_analysis_time = total_analysis_time / successful_analyses if successful_analyses > 0 else 0
            
            return {
                "test_name": "End-to-End Analysis",
                "success": successful_analyses > 0,
                "total_queries": len(self.test_queries),
                "successful_analyses": successful_analyses,
                "failed_analyses": len(self.test_queries) - successful_analyses,
                "success_rate": successful_analyses / len(self.test_queries) * 100,
                "average_analysis_time_ms": avg_analysis_time * 1000,
                "total_analysis_time_seconds": total_analysis_time,
                "analysis_results": analysis_results
            }
            
        except Exception as e:
            return {
                "test_name": "End-to-End Analysis",
                "success": False,
                "error": str(e)
            }
    
    async def _test_performance_comparison(self) -> Dict[str, Any]:
        """Compare performance between trained models and Epic 1 fallback."""
        logger.info("🧪 Testing performance comparison...")
        
        try:
            # Test with trained models
            trained_adapter = EpicMLAdapter(model_dir=str(self.model_dir))
            
            # Test with original Epic 1
            original_analyzer = Epic1MLAnalyzer()
            
            test_query = self.test_queries[1]  # Medium complexity query
            
            # Test trained model performance
            trained_start = time.time()
            trained_result = await trained_adapter.analyze(test_query, mode='hybrid')
            trained_time = time.time() - trained_start
            
            # Test original Epic 1 performance
            original_start = time.time()
            original_result = await original_analyzer.analyze(test_query, mode='hybrid')
            original_time = time.time() - original_start
            
            # Calculate performance metrics
            speedup_factor = original_time / trained_time if trained_time > 0 else 0
            
            return {
                "test_name": "Performance Comparison",
                "success": True,
                "test_query": test_query[:50] + "..." if len(test_query) > 50 else test_query,
                "trained_model_results": {
                    "analysis_time_ms": trained_time * 1000,
                    "complexity_score": trained_result.complexity_score,
                    "complexity_level": trained_result.complexity_level.value if hasattr(trained_result.complexity_level, 'value') else str(trained_result.complexity_level),
                    "confidence": trained_result.confidence,
                    "trained_models_used": trained_result.metadata.get('trained_models_used', False)
                },
                "original_epic1_results": {
                    "analysis_time_ms": original_time * 1000,
                    "complexity_score": original_result.complexity_score,
                    "complexity_level": original_result.complexity_level.value if hasattr(original_result.complexity_level, 'value') else str(original_result.complexity_level),
                    "confidence": original_result.confidence
                },
                "performance_metrics": {
                    "speedup_factor": speedup_factor,
                    "trained_faster": trained_time < original_time,
                    "time_difference_ms": (original_time - trained_time) * 1000
                }
            }
            
        except Exception as e:
            return {
                "test_name": "Performance Comparison",
                "success": False,
                "error": str(e)
            }
    
    async def _test_fallback_mechanism(self) -> Dict[str, Any]:
        """Test fallback to Epic 1 infrastructure when trained models fail."""
        logger.info("🧪 Testing fallback mechanism...")
        
        try:
            # Create adapter with intentionally bad model directory
            adapter_with_bad_models = EpicMLAdapter(model_dir="nonexistent_models")
            
            test_query = self.test_queries[0]  # Simple query
            
            # Attempt analysis (should fallback to Epic 1)
            result = await adapter_with_bad_models.analyze(test_query, mode='hybrid')
            
            # Check if fallback was used
            fallback_used = not result.metadata.get('trained_models_used', True)
            fallback_reason = result.metadata.get('fallback_reason', 'unknown')
            
            # Test algorithmic mode (should always use fallback)
            algorithmic_result = await adapter_with_bad_models.analyze(test_query, mode='algorithmic')
            algorithmic_fallback = not algorithmic_result.metadata.get('trained_models_used', True)
            
            return {
                "test_name": "Fallback Mechanism",
                "success": True,
                "test_query": test_query,
                "bad_model_dir_fallback": {
                    "fallback_used": fallback_used,
                    "fallback_reason": fallback_reason,
                    "result_obtained": result.complexity_score is not None,
                    "complexity_score": result.complexity_score,
                    "confidence": result.confidence
                },
                "algorithmic_mode_fallback": {
                    "fallback_used": algorithmic_fallback,
                    "result_obtained": algorithmic_result.complexity_score is not None,
                    "complexity_score": algorithmic_result.complexity_score,
                    "confidence": algorithmic_result.confidence
                },
                "fallback_reliability": fallback_used and algorithmic_fallback
            }
            
        except Exception as e:
            return {
                "test_name": "Fallback Mechanism",
                "success": False,
                "error": str(e)
            }
    
    async def _test_configuration_integration(self) -> Dict[str, Any]:
        """Test integration with configuration system."""
        logger.info("🧪 Testing configuration integration...")
        
        try:
            # Test loading configuration
            config_path = self.config_dir / "epic1_trained_ml_analyzer.yaml"
            
            if config_path.exists():
                config = load_config(config_path)
                
                # Extract Epic ML Adapter configuration
                query_processor_config = config.get('query_processor', {})
                analyzer_config = query_processor_config.get('config', {}).get('analyzer_config', {})
                
                # Initialize adapter with configuration
                adapter = EpicMLAdapter(config=analyzer_config)
                
                # Test configuration application
                test_query = self.test_queries[2]  # Complex query
                result = await adapter.analyze(test_query, mode='hybrid')
                
                return {
                    "test_name": "Configuration Integration",
                    "success": True,
                    "config_file_exists": True,
                    "config_loaded": config is not None,
                    "analyzer_config_present": bool(analyzer_config),
                    "adapter_initialized": adapter is not None,
                    "analysis_successful": result.complexity_score is not None,
                    "configuration_details": {
                        "memory_budget_gb": analyzer_config.get('memory_budget_gb'),
                        "parallel_execution": analyzer_config.get('parallel_execution'),
                        "fallback_strategy": analyzer_config.get('fallback_strategy'),
                        "model_dir": analyzer_config.get('model_dir')
                    },
                    "test_result": {
                        "complexity_score": result.complexity_score,
                        "complexity_level": result.complexity_level.value if hasattr(result.complexity_level, 'value') else str(result.complexity_level),
                        "confidence": result.confidence
                    }
                }
            else:
                return {
                    "test_name": "Configuration Integration",
                    "success": False,
                    "error": f"Configuration file not found: {config_path}",
                    "config_file_exists": False
                }
                
        except Exception as e:
            return {
                "test_name": "Configuration Integration",
                "success": False,
                "error": str(e)
            }
    
    def _check_model_files(self) -> Dict[str, bool]:
        """Check if required model files exist."""
        required_files = [
            "epic1_predictor.py",
            "epic1_system_config.json",
            "technical_model.pth",
            "linguistic_model.pth", 
            "task_model.pth",
            "semantic_model.pth",
            "computational_model.pth"
        ]
        
        file_status = {}
        for file_name in required_files:
            file_path = self.model_dir / file_name
            file_status[file_name] = file_path.exists()
        
        return file_status
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate overall test summary."""
        test_results = self.results.get("test_results", {})
        
        total_tests = len(test_results)
        successful_tests = len([t for t in test_results.values() if t.get("success", False)])
        
        # Key metrics
        models_available = test_results.get("trained_model_availability", {}).get("success", False)
        end_to_end_working = test_results.get("end_to_end_analysis", {}).get("success", False)
        fallback_working = test_results.get("fallback_mechanism", {}).get("success", False)
        config_integration_working = test_results.get("configuration_integration", {}).get("success", False)
        
        # Performance metrics
        avg_analysis_time = test_results.get("end_to_end_analysis", {}).get("average_analysis_time_ms", 0)
        success_rate = test_results.get("end_to_end_analysis", {}).get("success_rate", 0)
        
        # Overall status
        integration_ready = (
            models_available and 
            end_to_end_working and 
            fallback_working and 
            successful_tests >= total_tests * 0.8  # 80% tests passing
        )
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "test_success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "integration_ready": integration_ready,
            "key_capabilities": {
                "trained_models_available": models_available,
                "end_to_end_analysis_working": end_to_end_working,
                "fallback_mechanism_working": fallback_working,
                "configuration_integration_working": config_integration_working
            },
            "performance_summary": {
                "average_analysis_time_ms": avg_analysis_time,
                "query_success_rate": success_rate,
                "performance_target_met": avg_analysis_time < 50  # Under 50ms target
            },
            "recommendation": (
                "✅ Epic 1 integration ready for production deployment" if integration_ready 
                else "⚠️  Epic 1 integration needs attention before production deployment"
            )
        }
    
    def save_results(self, filename: Optional[str] = None) -> Path:
        """Save test results to JSON file."""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"epic1_trained_model_integration_test_results_{timestamp}.json"
        
        results_path = Path(filename)
        
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"📊 Test results saved to: {results_path}")
        return results_path


async def main():
    """Run Epic 1 trained model integration test."""
    print("🚀 Epic 1 Trained Model Integration Test")
    print("Testing trained PyTorch models with Epic 1 Infrastructure Bridge")
    print("=" * 80)
    
    tester = Epic1IntegrationTester()
    
    try:
        # Run comprehensive test
        results = await tester.run_comprehensive_test()
        
        # Save results
        results_path = tester.save_results()
        
        # Print summary
        summary = results.get("overall_summary", {})
        print(f"\n📊 Test Summary:")
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Successful Tests: {summary.get('successful_tests', 0)}")
        print(f"Test Success Rate: {summary.get('test_success_rate', 0):.1f}%")
        print(f"Integration Ready: {summary.get('integration_ready', False)}")
        print(f"Average Analysis Time: {summary.get('performance_summary', {}).get('average_analysis_time_ms', 0):.1f}ms")
        print(f"Query Success Rate: {summary.get('performance_summary', {}).get('query_success_rate', 0):.1f}%")
        print(f"\n{summary.get('recommendation', 'No recommendation available')}")
        
        print(f"\n📄 Detailed results saved to: {results_path}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        print(f"❌ Test failed with error: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    asyncio.run(main())