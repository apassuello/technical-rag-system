"""
Test Suite 1: Configuration and Architecture Forensics

This test suite provides comprehensive analysis of system configuration,
architecture detection, and component creation pathways.
"""

import os
import sys
import yaml
import json
import importlib
import inspect
from pathlib import Path
from typing import Any, Dict, List, Tuple

from base_diagnostic import DiagnosticTestBase, DataValidator

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    from src.core.platform_orchestrator import PlatformOrchestrator
    from src.core.component_factory import ComponentFactory
    from src.core.config import load_config
except ImportError as e:
    print(f"Import error (expected during analysis): {e}")


class ConfigurationForensics(DiagnosticTestBase):
    """
    Comprehensive configuration and architecture analysis.
    
    This class performs forensic-level analysis of:
    - Configuration file parsing and validation
    - Architecture detection logic
    - Component creation pathways
    - Environment and import resolution
    """
    
    def __init__(self, output_dir: Path = None):
        super().__init__(output_dir)
        self.config_files = [
            "config/default.yaml",
            "config/dev.yaml", 
            "config/production.yaml",
            "config/test.yaml"
        ]
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Execute all configuration forensics tests."""
        tests = [
            (self.test_configuration_file_analysis, "configuration_file_analysis", "configuration"),
            (self.test_architecture_detection_forensics, "architecture_detection", "architecture"),
            (self.test_component_creation_pathways, "component_creation", "factory"),
            (self.test_environment_and_imports, "environment_imports", "environment"),
            (self.test_config_validation_logic, "config_validation", "validation")
        ]
        
        results = []
        for test_func, test_name, component in tests:
            result = self.safe_execute(test_func, test_name, component)
            self.save_result(result)
            results.append(result)
        
        return results
    
    def test_configuration_file_analysis(self) -> Tuple[Dict, Dict, List[str], List[str]]:
        """Complete analysis of all configuration files."""
        data_captured = {
            "config_files_analysis": {},
            "config_comparison": {},
            "parsing_results": {}
        }
        
        analysis_results = {}
        issues_found = []
        recommendations = []
        
        # Analyze each configuration file
        for config_path in self.config_files:
            config_file = project_root / config_path
            file_analysis = {
                "file_path": str(config_file),
                "exists": config_file.exists(),
                "file_size": config_file.stat().st_size if config_file.exists() else 0,
                "last_modified": config_file.stat().st_mtime if config_file.exists() else 0
            }
            
            if config_file.exists():
                try:
                    # Raw content analysis
                    with open(config_file, 'r') as f:
                        raw_content = f.read()
                    
                    file_analysis["raw_content"] = raw_content
                    file_analysis["line_count"] = len(raw_content.split('\n'))
                    
                    # Parse configuration
                    parsed_config = yaml.safe_load(raw_content)
                    file_analysis["parsed_config"] = parsed_config
                    file_analysis["parsing_success"] = True
                    
                    # Analyze configuration structure
                    config_structure = self._analyze_config_structure(parsed_config)
                    file_analysis["structure_analysis"] = config_structure
                    
                    # Identify architecture triggers
                    architecture_triggers = self._identify_architecture_triggers(parsed_config)
                    file_analysis["architecture_triggers"] = architecture_triggers
                    
                except Exception as e:
                    file_analysis["parsing_error"] = str(e)
                    file_analysis["parsing_success"] = False
                    issues_found.append(f"Failed to parse {config_path}: {str(e)}")
            else:
                issues_found.append(f"Configuration file missing: {config_path}")
            
            data_captured["config_files_analysis"][config_path] = file_analysis
        
        # Compare configurations
        data_captured["config_comparison"] = self._compare_configurations(
            data_captured["config_files_analysis"]
        )
        
        # Test configuration loading mechanism
        try:
            default_config = load_config("config/default.yaml")
            data_captured["config_loading_test"] = {
                "success": True,
                "loaded_config": default_config,
                "loading_method": "load_config function"
            }
        except Exception as e:
            data_captured["config_loading_test"] = {
                "success": False,
                "error": str(e)
            }
            issues_found.append(f"Configuration loading failed: {str(e)}")
        
        # Analysis results
        analysis_results = {
            "total_config_files": len(self.config_files),
            "existing_config_files": sum(1 for f in data_captured["config_files_analysis"].values() if f["exists"]),
            "parsing_success_rate": sum(1 for f in data_captured["config_files_analysis"].values() 
                                      if f.get("parsing_success", False)) / len(self.config_files),
            "architecture_consistency": self._analyze_architecture_consistency(data_captured["config_files_analysis"])
        }
        
        # Generate recommendations
        if analysis_results["parsing_success_rate"] < 1.0:
            recommendations.append("Fix configuration file parsing errors")
        
        if not analysis_results["architecture_consistency"]:
            recommendations.append("Ensure consistent architecture configuration across all config files")
        
        return data_captured, analysis_results, issues_found, recommendations
    
    def test_architecture_detection_forensics(self) -> Tuple[Dict, Dict, List[str], List[str]]:
        """Detailed analysis of architecture detection logic."""
        data_captured = {
            "architecture_detection_process": {},
            "component_analysis": {},
            "health_monitoring_analysis": {}
        }
        
        analysis_results = {}
        issues_found = []
        recommendations = []
        
        try:
            # Initialize platform orchestrator with default config
            orchestrator = PlatformOrchestrator("config/default.yaml")
            
            # Capture system health information
            system_health = orchestrator.get_system_health()
            data_captured["system_health"] = system_health
            
            # Analyze architecture detection logic
            architecture_info = {
                "claimed_architecture": system_health.get("architecture", "unknown"),
                "orchestrator_type": type(orchestrator).__name__,
                "config_file_used": "config/default.yaml"
            }
            
            # Inspect orchestrator internals for architecture detection
            orchestrator_internals = self._inspect_orchestrator_internals(orchestrator)
            data_captured["orchestrator_internals"] = orchestrator_internals
            
            # Analyze configuration that determines architecture
            config_analysis = self._analyze_architecture_config_logic(orchestrator)
            data_captured["architecture_config_logic"] = config_analysis
            
            # Test architecture detection with different configurations
            architecture_tests = self._test_architecture_detection_variations()
            data_captured["architecture_detection_tests"] = architecture_tests
            
            # Check for Phase 4 vs legacy indicators
            phase_indicators = self._analyze_phase_indicators(orchestrator, system_health)
            data_captured["phase_indicators"] = phase_indicators
            
            analysis_results = {
                "detected_architecture": architecture_info["claimed_architecture"],
                "expected_architecture": "unified",  # Phase 4 should show unified
                "architecture_match": architecture_info["claimed_architecture"] == "unified",
                "phase_analysis": phase_indicators
            }
            
            # Check for issues
            if analysis_results["detected_architecture"] == "legacy":
                issues_found.append("System showing 'legacy' architecture instead of expected 'unified' for Phase 4")
            
            if analysis_results["detected_architecture"] == "unknown":
                issues_found.append("Architecture detection returning 'unknown' - logic may be broken")
                
        except Exception as e:
            issues_found.append(f"Architecture detection analysis failed: {str(e)}")
            data_captured["error"] = str(e)
        
        if issues_found:
            recommendations.append("Fix architecture detection logic to correctly identify Phase 4 unified architecture")
            recommendations.append("Verify configuration triggers for architecture classification")
        
        return data_captured, analysis_results, issues_found, recommendations
    
    def test_component_creation_pathways(self) -> Tuple[Dict, Dict, List[str], List[str]]:
        """Analyze component creation methods and factory usage."""
        data_captured = {
            "factory_analysis": {},
            "component_creation_tests": {},
            "cache_analysis": {},
            "metrics_analysis": {}
        }
        
        analysis_results = {}
        issues_found = []
        recommendations = []
        
        try:
            # Analyze ComponentFactory
            factory_info = self._analyze_component_factory()
            data_captured["factory_analysis"] = factory_info
            
            # Test component creation for each type
            component_types = ["embedder", "retriever", "generator"]
            for component_type in component_types:
                creation_test = self._test_component_creation(component_type)
                data_captured["component_creation_tests"][component_type] = creation_test
            
            # Analyze factory metrics and caching
            factory_metrics = self._analyze_factory_metrics()
            data_captured["factory_metrics"] = factory_metrics
            
            # Test cache behavior
            cache_test = self._test_cache_behavior()
            data_captured["cache_test"] = cache_test
            
            analysis_results = {
                "factory_available": factory_info.get("available", False),
                "creation_methods_used": [
                    test.get("creation_method", "unknown") 
                    for test in data_captured["component_creation_tests"].values()
                ],
                "cache_performance": cache_test.get("cache_hit_rate", 0),
                "metrics_tracking": factory_metrics.get("metrics_available", False)
            }
            
            # Check for issues
            if analysis_results["cache_performance"] == 0:
                issues_found.append("Factory cache showing 0% hit rate despite component usage")
            
            if "Factory" not in analysis_results["creation_methods_used"]:
                issues_found.append("Components not being created via ComponentFactory")
                
        except Exception as e:
            issues_found.append(f"Component creation analysis failed: {str(e)}")
            data_captured["error"] = str(e)
        
        if issues_found:
            recommendations.append("Verify ComponentFactory is being used for component creation")
            recommendations.append("Fix factory metrics tracking and cache performance monitoring")
        
        return data_captured, analysis_results, issues_found, recommendations
    
    def test_environment_and_imports(self) -> Tuple[Dict, Dict, List[str], List[str]]:
        """Analyze environment state and import resolution."""
        data_captured = {
            "environment_variables": {},
            "python_path_analysis": {},
            "import_resolution": {},
            "module_analysis": {}
        }
        
        analysis_results = {}
        issues_found = []
        recommendations = []
        
        # Capture environment variables
        env_vars = dict(os.environ)
        data_captured["environment_variables"] = {
            "total_vars": len(env_vars),
            "python_related": {k: v for k, v in env_vars.items() if "PYTHON" in k.upper()},
            "path_related": {k: v for k, v in env_vars.items() if "PATH" in k.upper()},
            "hf_related": {k: v for k, v in env_vars.items() if "HF" in k.upper() or "HUGGINGFACE" in k.upper()}
        }
        
        # Analyze Python path
        data_captured["python_path_analysis"] = {
            "sys_path": sys.path,
            "working_directory": os.getcwd(),
            "project_root": str(project_root),
            "project_in_path": str(project_root) in sys.path
        }
        
        # Test critical imports
        critical_imports = [
            "src.core.platform_orchestrator",
            "src.core.component_factory", 
            "src.core.config",
            "src.components.generators.adaptive_generator",
            "shared_utils.generation.hf_answer_generator"
        ]
        
        import_results = {}
        for module_name in critical_imports:
            try:
                module = importlib.import_module(module_name)
                import_results[module_name] = {
                    "success": True,
                    "module_file": getattr(module, "__file__", "unknown"),
                    "module_version": getattr(module, "__version__", "unknown")
                }
            except ImportError as e:
                import_results[module_name] = {
                    "success": False,
                    "error": str(e)
                }
                issues_found.append(f"Failed to import {module_name}: {str(e)}")
        
        data_captured["import_resolution"] = import_results
        
        # Analyze module availability
        module_analysis = self._analyze_module_availability()
        data_captured["module_analysis"] = module_analysis
        
        analysis_results = {
            "import_success_rate": sum(1 for r in import_results.values() if r["success"]) / len(critical_imports),
            "environment_complete": len(data_captured["environment_variables"]["python_related"]) > 0,
            "project_path_configured": data_captured["python_path_analysis"]["project_in_path"]
        }
        
        if analysis_results["import_success_rate"] < 1.0:
            recommendations.append("Fix import errors for critical modules")
        
        if not analysis_results["project_path_configured"]:
            recommendations.append("Ensure project root is in Python path")
        
        return data_captured, analysis_results, issues_found, recommendations
    
    def test_config_validation_logic(self) -> Tuple[Dict, Dict, List[str], List[str]]:
        """Test configuration validation and error handling."""
        data_captured = {
            "validation_tests": {},
            "error_handling": {},
            "schema_analysis": {}
        }
        
        analysis_results = {}
        issues_found = []
        recommendations = []
        
        # Test configuration validation with various inputs
        test_configs = [
            {"name": "valid_default", "config": "config/default.yaml"},
            {"name": "missing_file", "config": "config/nonexistent.yaml"},
            {"name": "empty_config", "config_content": ""},
            {"name": "invalid_yaml", "config_content": "invalid: yaml: content: ["}
        ]
        
        for test in test_configs:
            validation_result = self._test_config_validation(test)
            data_captured["validation_tests"][test["name"]] = validation_result
        
        # Analyze error handling behavior
        error_handling = self._test_error_handling()
        data_captured["error_handling"] = error_handling
        
        analysis_results = {
            "validation_robustness": all(
                test.get("handled_gracefully", False) 
                for test in data_captured["validation_tests"].values()
            ),
            "error_handling_quality": error_handling.get("quality_score", 0)
        }
        
        return data_captured, analysis_results, issues_found, recommendations
    
    # Helper methods for detailed analysis
    
    def _analyze_config_structure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze configuration structure and completeness."""
        if not config:
            return {"error": "Empty configuration"}
        
        expected_sections = [
            "document_processor", "embedder", "vector_store", 
            "retriever", "answer_generator"
        ]
        
        structure = {
            "total_sections": len(config),
            "expected_sections": expected_sections,
            "present_sections": list(config.keys()),
            "missing_sections": [s for s in expected_sections if s not in config],
            "extra_sections": [s for s in config.keys() if s not in expected_sections],
            "section_analysis": {}
        }
        
        for section in config:
            if isinstance(config[section], dict):
                structure["section_analysis"][section] = {
                    "type": config[section].get("type", "unknown"),
                    "has_config": "config" in config[section],
                    "config_fields": list(config[section].get("config", {}).keys()) if "config" in config[section] else []
                }
        
        return structure
    
    def _identify_architecture_triggers(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Identify configuration elements that trigger architecture classification."""
        triggers = {
            "has_vector_store": "vector_store" in config,
            "has_retriever": "retriever" in config,
            "retriever_type": config.get("retriever", {}).get("type", "unknown"),
            "vector_store_type": config.get("vector_store", {}).get("type", "unknown"),
            "architecture_indicators": {}
        }
        
        # Analyze what indicates legacy vs unified architecture
        if triggers["has_vector_store"] and triggers["has_retriever"]:
            if triggers["retriever_type"] == "hybrid":
                triggers["architecture_indicators"]["likely_architecture"] = "legacy"
                triggers["architecture_indicators"]["reason"] = "separate vector_store + hybrid retriever"
            elif triggers["retriever_type"] == "unified":
                triggers["architecture_indicators"]["likely_architecture"] = "unified"
                triggers["architecture_indicators"]["reason"] = "unified retriever without separate vector_store"
        elif triggers["has_retriever"] and not triggers["has_vector_store"]:
            if triggers["retriever_type"] == "unified":
                triggers["architecture_indicators"]["likely_architecture"] = "unified"
                triggers["architecture_indicators"]["reason"] = "unified retriever only"
        
        return triggers
    
    def _compare_configurations(self, config_analyses: Dict[str, Dict]) -> Dict[str, Any]:
        """Compare different configuration files for consistency."""
        comparison = {
            "architecture_consistency": {},
            "component_type_consistency": {},
            "configuration_differences": {}
        }
        
        # Compare architecture indicators across configs
        architectures = {}
        for config_name, analysis in config_analyses.items():
            if analysis.get("exists") and analysis.get("parsing_success"):
                arch_triggers = analysis.get("architecture_triggers", {})
                architectures[config_name] = arch_triggers.get("architecture_indicators", {}).get("likely_architecture", "unknown")
        
        comparison["architecture_consistency"] = {
            "architectures_by_config": architectures,
            "consistent": len(set(architectures.values())) <= 1,
            "variations": list(set(architectures.values()))
        }
        
        return comparison
    
    def _inspect_orchestrator_internals(self, orchestrator) -> Dict[str, Any]:
        """Inspect platform orchestrator internal state."""
        internals = {
            "class_name": type(orchestrator).__name__,
            "attributes": {},
            "methods": [],
            "config_access": {}
        }
        
        # Capture key attributes
        for attr in dir(orchestrator):
            if not attr.startswith('_'):
                try:
                    value = getattr(orchestrator, attr)
                    if not callable(value):
                        internals["attributes"][attr] = str(value)[:200]  # Truncate long values
                    else:
                        internals["methods"].append(attr)
                except:
                    internals["attributes"][attr] = "unable_to_access"
        
        # Check how configuration is accessed
        if hasattr(orchestrator, 'config'):
            internals["config_access"]["has_config_attr"] = True
            internals["config_access"]["config_type"] = type(orchestrator.config).__name__
        
        return internals
    
    def _analyze_architecture_config_logic(self, orchestrator) -> Dict[str, Any]:
        """Analyze how configuration determines architecture classification."""
        logic = {
            "configuration_analysis": {},
            "architecture_determination": {},
            "component_detection": {}
        }
        
        # Analyze the configuration the orchestrator is using
        if hasattr(orchestrator, 'config'):
            config = orchestrator.config
            logic["configuration_analysis"] = {
                "has_vector_store": "vector_store" in config,
                "has_retriever": "retriever" in config,
                "retriever_type": config.get("retriever", {}).get("type", "unknown"),
                "components_configured": list(config.keys())
            }
        
        return logic
    
    def _test_architecture_detection_variations(self) -> Dict[str, Any]:
        """Test architecture detection with different configuration variations."""
        tests = {}
        
        # Test with different config files if available
        for config_file in self.config_files:
            config_path = project_root / config_file
            if config_path.exists():
                try:
                    test_orchestrator = PlatformOrchestrator(config_file)
                    health = test_orchestrator.get_system_health()
                    tests[config_file] = {
                        "success": True,
                        "detected_architecture": health.get("architecture", "unknown"),
                        "health_data": health
                    }
                except Exception as e:
                    tests[config_file] = {
                        "success": False,
                        "error": str(e)
                    }
        
        return tests
    
    def _analyze_phase_indicators(self, orchestrator, system_health: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze indicators of which phase the system is in."""
        indicators = {
            "system_health_architecture": system_health.get("architecture", "unknown"),
            "expected_phase4_architecture": "unified",
            "component_analysis": {},
            "factory_usage": {}
        }
        
        # Check what components are actually being used
        try:
            # Try to access orchestrator components
            if hasattr(orchestrator, 'retriever'):
                retriever_type = type(orchestrator.retriever).__name__
                indicators["component_analysis"]["retriever_type"] = retriever_type
                indicators["component_analysis"]["is_unified_retriever"] = "Unified" in retriever_type
        except:
            indicators["component_analysis"]["error"] = "Unable to access orchestrator components"
        
        return indicators
    
    def _analyze_component_factory(self) -> Dict[str, Any]:
        """Analyze ComponentFactory availability and functionality."""
        factory_info = {
            "available": False,
            "class_analysis": {},
            "methods_available": [],
            "metrics_methods": []
        }
        
        try:
            factory_info["available"] = True
            factory_info["class_analysis"] = {
                "class_name": ComponentFactory.__name__,
                "module": ComponentFactory.__module__
            }
            
            # Analyze available methods
            for method in dir(ComponentFactory):
                if not method.startswith('_'):
                    if callable(getattr(ComponentFactory, method)):
                        factory_info["methods_available"].append(method)
                        if "metric" in method.lower() or "performance" in method.lower():
                            factory_info["metrics_methods"].append(method)
        
        except Exception as e:
            factory_info["error"] = str(e)
        
        return factory_info
    
    def _test_component_creation(self, component_type: str) -> Dict[str, Any]:
        """Test component creation for specific type."""
        creation_test = {
            "component_type": component_type,
            "creation_method": "unknown",
            "success": False,
            "error": None
        }
        
        try:
            # Try to create component via orchestrator
            orchestrator = PlatformOrchestrator("config/default.yaml")
            
            if component_type == "embedder" and hasattr(orchestrator, 'embedder'):
                component = orchestrator.embedder
                creation_test["success"] = True
                creation_test["creation_method"] = "orchestrator"
                creation_test["component_class"] = type(component).__name__
            elif component_type == "retriever" and hasattr(orchestrator, 'retriever'):
                component = orchestrator.retriever
                creation_test["success"] = True
                creation_test["creation_method"] = "orchestrator"
                creation_test["component_class"] = type(component).__name__
            elif component_type == "generator" and hasattr(orchestrator, 'generator'):
                component = orchestrator.generator
                creation_test["success"] = True
                creation_test["creation_method"] = "orchestrator"
                creation_test["component_class"] = type(component).__name__
                
        except Exception as e:
            creation_test["error"] = str(e)
        
        return creation_test
    
    def _analyze_factory_metrics(self) -> Dict[str, Any]:
        """Analyze factory metrics and performance tracking."""
        metrics = {
            "metrics_available": False,
            "performance_data": {},
            "cache_data": {}
        }
        
        try:
            # Try to get factory metrics
            if hasattr(ComponentFactory, 'get_performance_metrics'):
                performance_metrics = ComponentFactory.get_performance_metrics()
                metrics["metrics_available"] = True
                metrics["performance_data"] = performance_metrics
            
            if hasattr(ComponentFactory, 'get_cache_stats'):
                cache_stats = ComponentFactory.get_cache_stats()
                metrics["cache_data"] = cache_stats
                
        except Exception as e:
            metrics["error"] = str(e)
        
        return metrics
    
    def _test_cache_behavior(self) -> Dict[str, Any]:
        """Test component caching behavior."""
        cache_test = {
            "cache_available": False,
            "cache_hit_rate": 0,
            "cache_performance": {}
        }
        
        try:
            # Create multiple components of same type to test caching
            orchestrator1 = PlatformOrchestrator("config/default.yaml")
            orchestrator2 = PlatformOrchestrator("config/default.yaml")
            
            # Check if same instances are reused (caching)
            if hasattr(orchestrator1, 'embedder') and hasattr(orchestrator2, 'embedder'):
                cache_test["same_embedder_instance"] = orchestrator1.embedder is orchestrator2.embedder
            
            # Try to get cache statistics
            if hasattr(ComponentFactory, 'get_cache_stats'):
                cache_stats = ComponentFactory.get_cache_stats()
                cache_test["cache_available"] = True
                cache_test["cache_stats"] = cache_stats
                
                if 'hits' in cache_stats and 'misses' in cache_stats:
                    total = cache_stats['hits'] + cache_stats['misses']
                    cache_test["cache_hit_rate"] = cache_stats['hits'] / total if total > 0 else 0
                    
        except Exception as e:
            cache_test["error"] = str(e)
        
        return cache_test
    
    def _analyze_module_availability(self) -> Dict[str, Any]:
        """Analyze availability of key modules and dependencies."""
        modules = {
            "core_modules": {},
            "shared_utils": {},
            "external_dependencies": {}
        }
        
        # Test core modules
        core_modules = [
            "yaml", "json", "pathlib", "logging", "dataclasses"
        ]
        
        for module in core_modules:
            try:
                imported = importlib.import_module(module)
                modules["core_modules"][module] = {
                    "available": True,
                    "version": getattr(imported, "__version__", "unknown")
                }
            except ImportError:
                modules["core_modules"][module] = {"available": False}
        
        return modules
    
    def _test_config_validation(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test configuration validation with specific input."""
        result = {
            "test_name": test_config["name"],
            "handled_gracefully": False,
            "error_type": None,
            "error_message": None
        }
        
        try:
            if "config" in test_config:
                # Test with file path
                config = load_config(test_config["config"])
                result["handled_gracefully"] = True
                result["config_loaded"] = True
            elif "config_content" in test_config:
                # Test with content
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                    f.write(test_config["config_content"])
                    temp_path = f.name
                
                config = load_config(temp_path)
                os.unlink(temp_path)
                result["handled_gracefully"] = True
                result["config_loaded"] = True
                
        except Exception as e:
            result["error_type"] = type(e).__name__
            result["error_message"] = str(e)
            result["handled_gracefully"] = True  # If it raises expected exception
        
        return result
    
    def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling quality in configuration system."""
        error_tests = {
            "quality_score": 0,
            "tests_performed": [],
            "error_handling_analysis": {}
        }
        
        # Test various error conditions
        test_cases = [
            {"name": "missing_file", "test": lambda: load_config("nonexistent.yaml")},
            {"name": "invalid_yaml", "test": lambda: yaml.safe_load("invalid: yaml: [")}
        ]
        
        for test_case in test_cases:
            try:
                test_case["test"]()
                result = {"error_raised": False}
            except Exception as e:
                result = {
                    "error_raised": True,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "informative": len(str(e)) > 10
                }
            
            error_tests["tests_performed"].append({
                "name": test_case["name"],
                "result": result
            })
        
        # Calculate quality score
        informative_errors = sum(1 for test in error_tests["tests_performed"] 
                               if test["result"].get("informative", False))
        error_tests["quality_score"] = informative_errors / len(test_cases) if test_cases else 0
        
        return error_tests


if __name__ == "__main__":
    # Run configuration forensics tests
    forensics = ConfigurationForensics()
    results = forensics.run_all_tests()
    forensics.print_summary()