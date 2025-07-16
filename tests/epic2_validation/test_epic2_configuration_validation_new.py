"""
Epic 2 Configuration Validation Tests
=====================================

This module provides comprehensive validation for Epic 2 configuration files
that enable advanced features through YAML-driven sub-component activation
within ModularUnifiedRetriever.

Test Categories:
1. Schema validation for all Epic 2 configuration files
2. Sub-component instantiation verification (NeuralReranker vs IdentityReranker)
3. Configuration parameter propagation testing
4. Invalid configuration error handling
5. Feature activation confirmation
6. Configuration consistency validation

Architecture Reality:
- Epic 2 features are sub-components within ModularUnifiedRetriever
- Features activated through YAML configuration, not standalone components
- ComponentFactory transforms configuration to correct sub-component types
- Tests validate configuration-driven feature activation, not direct instantiation

Configuration Files Tested:
- test_epic2_base.yaml - Basic configuration (no Epic 2 features)
- test_epic2_neural_enabled.yaml - Neural reranking sub-component only
- test_epic2_graph_enabled.yaml - Graph enhancement sub-component only
- test_epic2_all_features.yaml - All Epic 2 sub-components enabled
- test_epic2_minimal.yaml - Minimal features configuration
"""

import pytest
import logging
import time
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock
import yaml

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import Epic 2 components and infrastructure
from src.core.config import load_config
from src.core.component_factory import ComponentFactory
from src.components.retrievers.modular_unified_retriever import ModularUnifiedRetriever
from src.components.retrievers.rerankers.neural_reranker import NeuralReranker
from src.components.retrievers.rerankers.identity_reranker import IdentityReranker
from src.components.retrievers.fusion.graph_enhanced_rrf_fusion import (
    GraphEnhancedRRFFusion,
)
from src.components.retrievers.fusion.rrf_fusion import RRFFusion
from src.components.retrievers.indices.faiss_index import FAISSIndex
from src.components.retrievers.indices.weaviate_index import WeaviateIndex
from src.components.embedders.modular_embedder import ModularEmbedder

logger = logging.getLogger(__name__)


class Epic2ConfigurationValidator:
    """
    Comprehensive validator for Epic 2 configuration files.

    Validates YAML-driven feature activation and ensures proper sub-component
    instantiation within ModularUnifiedRetriever architecture.
    """

    def __init__(self):
        """Initialize configuration validator."""
        self.test_results = {}
        self.validation_errors = []
        self.performance_metrics = {}

        # Define Epic 2 test configuration files
        self.config_files = {
            "base": "test_epic2_base.yaml",
            "neural_enabled": "test_epic2_neural_enabled.yaml",
            "graph_enabled": "test_epic2_graph_enabled.yaml",
            "all_features": "test_epic2_all_features.yaml",
            "minimal": "test_epic2_minimal.yaml",
        }

        # Expected sub-component mappings
        self.expected_mappings = {
            "base": {
                "reranker": "NeuralReranker",  # base config has neural enabled
                "fusion": "GraphEnhancedRRFFusion",  # base config has graph enabled
                "vector_index": "FAISSIndex",
            },
            "neural_enabled": {
                "reranker": "NeuralReranker",
                "fusion": "RRFFusion",  # graph disabled
                "vector_index": "FAISSIndex",
            },
            "graph_enabled": {
                "reranker": "IdentityReranker",  # neural disabled
                "fusion": "GraphEnhancedRRFFusion",
                "vector_index": "FAISSIndex",
            },
            "all_features": {
                "reranker": "NeuralReranker",
                "fusion": "GraphEnhancedRRFFusion",
                "vector_index": "FAISSIndex",
            },
            "minimal": {
                "reranker": "IdentityReranker",  # neural disabled
                "fusion": "RRFFusion",  # graph disabled
                "vector_index": "FAISSIndex",
            },
        }

    def run_all_validations(self) -> Dict[str, Any]:
        """Run comprehensive configuration validation tests."""
        logger.info("Starting Epic 2 configuration validation tests...")

        try:
            # Test 1: Schema validation
            self.test_results["schema_validation"] = self._test_schema_validation()

            # Test 2: Configuration parsing
            self.test_results["configuration_parsing"] = (
                self._test_configuration_parsing()
            )

            # Test 3: Sub-component instantiation
            self.test_results["subcomponent_instantiation"] = (
                self._test_subcomponent_instantiation()
            )

            # Test 4: Parameter propagation
            self.test_results["parameter_propagation"] = (
                self._test_parameter_propagation()
            )

            # Test 5: Feature activation
            self.test_results["feature_activation"] = self._test_feature_activation()

            # Test 6: Error handling
            self.test_results["error_handling"] = self._test_error_handling()

            # Calculate overall score
            passed_tests = sum(
                1
                for result in self.test_results.values()
                if result.get("passed", False)
            )
            total_tests = len(self.test_results)
            overall_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

            return {
                "overall_score": overall_score,
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "test_results": self.test_results,
                "performance_metrics": self.performance_metrics,
                "validation_errors": self.validation_errors,
            }

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            self.validation_errors.append(f"Critical validation failure: {e}")
            return {
                "overall_score": 0,
                "passed_tests": 0,
                "total_tests": len(self.test_results),
                "test_results": self.test_results,
                "performance_metrics": self.performance_metrics,
                "validation_errors": self.validation_errors,
            }

    def _load_config_file(self, config_name: str) -> Any:
        """Load configuration file by name."""
        config_path = Path(f"config/{config_name}")
        return load_config(config_path)

    def _test_schema_validation(self) -> Dict[str, Any]:
        """Test configuration schema compliance for all Epic 2 configs."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing configuration schema validation...")

            schema_results = {}

            for config_type, config_file in self.config_files.items():
                try:
                    # Load configuration
                    config = self._load_config_file(config_file)

                    # Validate required top-level sections
                    required_sections = [
                        "retriever",
                        "embedder",
                        "document_processor",
                        "answer_generator",
                    ]
                    missing_sections = []

                    for section in required_sections:
                        if (
                            not hasattr(config, section)
                            or getattr(config, section) is None
                        ):
                            missing_sections.append(section)

                    # Validate retriever configuration structure
                    retriever_config = config.retriever
                    if retriever_config.type != "modular_unified":
                        missing_sections.append(
                            f"retriever.type should be 'modular_unified', got '{retriever_config.type}'"
                        )

                    # Validate sub-component configuration presence
                    retriever_sub_config = retriever_config.config
                    required_sub_components = [
                        "vector_index",
                        "sparse",
                        "fusion",
                        "reranker",
                    ]

                    for sub_component in required_sub_components:
                        if sub_component not in retriever_sub_config:
                            missing_sections.append(f"retriever.config.{sub_component}")

                    schema_results[config_type] = {
                        "valid": len(missing_sections) == 0,
                        "missing_sections": missing_sections,
                        "config_file": config_file,
                    }

                except Exception as e:
                    schema_results[config_type] = {
                        "valid": False,
                        "error": str(e),
                        "config_file": config_file,
                    }

            # Check if all configurations are valid
            all_valid = all(
                result.get("valid", False) for result in schema_results.values()
            )

            test_result.update(
                {
                    "passed": all_valid,
                    "details": {
                        "schema_results": schema_results,
                        "configs_tested": len(self.config_files),
                        "valid_configs": sum(
                            1 for r in schema_results.values() if r.get("valid", False)
                        ),
                    },
                }
            )

            if not all_valid:
                test_result["errors"].append(
                    "Some configuration files failed schema validation"
                )

        except Exception as e:
            test_result["errors"].append(f"Schema validation failed: {e}")
            logger.error(f"Schema validation error: {e}")

        return test_result

    def _test_configuration_parsing(self) -> Dict[str, Any]:
        """Test YAML parsing correctness for all configurations."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing configuration parsing...")

            parsing_results = {}

            for config_type, config_file in self.config_files.items():
                start_time = time.time()

                try:
                    # Test YAML parsing
                    config = self._load_config_file(config_file)
                    parsing_time = time.time() - start_time

                    # Validate basic structure
                    has_retriever = (
                        hasattr(config, "retriever") and config.retriever is not None
                    )
                    has_embedder = (
                        hasattr(config, "embedder") and config.embedder is not None
                    )

                    parsing_results[config_type] = {
                        "parsed": True,
                        "parsing_time_ms": parsing_time * 1000,
                        "has_retriever": has_retriever,
                        "has_embedder": has_embedder,
                        "retriever_type": (
                            getattr(config.retriever, "type", None)
                            if has_retriever
                            else None
                        ),
                    }

                except Exception as e:
                    parsing_results[config_type] = {
                        "parsed": False,
                        "error": str(e),
                        "parsing_time_ms": (time.time() - start_time) * 1000,
                    }

            # Check if all configurations parsed successfully
            all_parsed = all(
                result.get("parsed", False) for result in parsing_results.values()
            )

            test_result.update(
                {
                    "passed": all_parsed,
                    "details": {
                        "parsing_results": parsing_results,
                        "average_parsing_time_ms": sum(
                            r.get("parsing_time_ms", 0)
                            for r in parsing_results.values()
                        )
                        / len(parsing_results),
                    },
                }
            )

            if not all_parsed:
                test_result["errors"].append("Some configuration files failed to parse")

        except Exception as e:
            test_result["errors"].append(f"Configuration parsing test failed: {e}")
            logger.error(f"Configuration parsing error: {e}")

        return test_result

    def _test_subcomponent_instantiation(self) -> Dict[str, Any]:
        """Test correct sub-component instantiation from configuration."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing sub-component instantiation...")

            instantiation_results = {}

            for config_type, config_file in self.config_files.items():
                try:
                    # Load configuration and create embedder (required for retriever)
                    config = self._load_config_file(config_file)

                    # Create embedder first (required dependency)
                    factory = ComponentFactory()
                    embedder = factory.create_embedder(
                        config.embedder.type, **config.embedder.config.dict()
                    )

                    # Create retriever through ComponentFactory
                    retriever = factory.create_retriever(
                        config.retriever.type,
                        embedder=embedder,
                        **config.retriever.config.dict(),
                    )

                    # Verify it's ModularUnifiedRetriever
                    is_modular = isinstance(retriever, ModularUnifiedRetriever)

                    # Check sub-component types
                    actual_components = {
                        "reranker": type(retriever.reranker).__name__,
                        "fusion": type(retriever.fusion_strategy).__name__,
                        "vector_index": type(retriever.vector_index).__name__,
                    }

                    expected_components = self.expected_mappings.get(config_type, {})

                    # Check if components match expectations
                    components_match = True
                    component_mismatches = []

                    for component_name, expected_type in expected_components.items():
                        actual_type = actual_components.get(component_name)
                        if actual_type != expected_type:
                            components_match = False
                            component_mismatches.append(
                                f"{component_name}: expected {expected_type}, got {actual_type}"
                            )

                    instantiation_results[config_type] = {
                        "instantiated": True,
                        "is_modular_unified": is_modular,
                        "actual_components": actual_components,
                        "expected_components": expected_components,
                        "components_match": components_match,
                        "mismatches": component_mismatches,
                    }

                except Exception as e:
                    instantiation_results[config_type] = {
                        "instantiated": False,
                        "error": str(e),
                    }

            # Check if all instantiations succeeded and components match
            all_instantiated = all(
                result.get("instantiated", False)
                for result in instantiation_results.values()
            )
            all_components_match = all(
                result.get("components_match", False)
                for result in instantiation_results.values()
                if result.get("instantiated", False)
            )

            test_result.update(
                {
                    "passed": all_instantiated and all_components_match,
                    "details": {
                        "instantiation_results": instantiation_results,
                        "configs_instantiated": sum(
                            1
                            for r in instantiation_results.values()
                            if r.get("instantiated", False)
                        ),
                        "configs_with_correct_components": sum(
                            1
                            for r in instantiation_results.values()
                            if r.get("components_match", False)
                        ),
                    },
                }
            )

            if not all_instantiated:
                test_result["errors"].append(
                    "Some configurations failed to instantiate"
                )
            if not all_components_match:
                test_result["errors"].append(
                    "Some configurations created wrong sub-component types"
                )

        except Exception as e:
            test_result["errors"].append(
                f"Sub-component instantiation test failed: {e}"
            )
            logger.error(f"Sub-component instantiation error: {e}")

        return test_result

    def _test_parameter_propagation(self) -> Dict[str, Any]:
        """Test configuration parameter propagation to sub-components."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing parameter propagation...")

            propagation_results = {}

            # Test specific configurations with known parameters
            test_configs = {
                "neural_enabled": {
                    "config_file": "test_epic2_neural_enabled.yaml",
                    "expected_params": {
                        "neural_model": "cross-encoder/ms-marco-MiniLM-L6-v2",
                        "neural_batch_size": 32,
                        "neural_max_candidates": 100,
                    },
                },
                "graph_enabled": {
                    "config_file": "test_epic2_graph_enabled.yaml",
                    "expected_params": {
                        "graph_similarity_threshold": 0.65,
                        "graph_max_connections": 15,
                        "graph_use_pagerank": True,
                    },
                },
            }

            for config_type, test_config in test_configs.items():
                try:
                    # Load configuration
                    config = self._load_config_file(test_config["config_file"])

                    # Create components
                    factory = ComponentFactory()
                    embedder = factory.create_embedder(
                        config.embedder.type, **config.embedder.config.dict()
                    )
                    retriever = factory.create_retriever(
                        config.retriever.type,
                        embedder=embedder,
                        **config.retriever.config.dict(),
                    )

                    param_checks = {}

                    if config_type == "neural_enabled":
                        # Check neural reranking parameters
                        if isinstance(retriever.reranker, NeuralReranker):
                            param_checks["neural_model"] = (
                                retriever.reranker.model_name
                                == test_config["expected_params"]["neural_model"]
                            )
                            param_checks["neural_batch_size"] = (
                                retriever.reranker.batch_size
                                == test_config["expected_params"]["neural_batch_size"]
                            )
                            param_checks["neural_max_candidates"] = (
                                retriever.reranker.max_candidates
                                == test_config["expected_params"][
                                    "neural_max_candidates"
                                ]
                            )

                    elif config_type == "graph_enabled":
                        # Check graph enhancement parameters
                        if isinstance(
                            retriever.fusion_strategy, GraphEnhancedRRFFusion
                        ):
                            param_checks["graph_similarity_threshold"] = (
                                retriever.fusion_strategy.similarity_threshold
                                == test_config["expected_params"][
                                    "graph_similarity_threshold"
                                ]
                            )
                            param_checks["graph_max_connections"] = (
                                retriever.fusion_strategy.max_connections_per_document
                                == test_config["expected_params"][
                                    "graph_max_connections"
                                ]
                            )
                            param_checks["graph_use_pagerank"] = (
                                retriever.fusion_strategy.use_pagerank
                                == test_config["expected_params"]["graph_use_pagerank"]
                            )

                    all_params_correct = all(param_checks.values())

                    propagation_results[config_type] = {
                        "tested": True,
                        "param_checks": param_checks,
                        "all_params_correct": all_params_correct,
                        "incorrect_params": [
                            param
                            for param, correct in param_checks.items()
                            if not correct
                        ],
                    }

                except Exception as e:
                    propagation_results[config_type] = {
                        "tested": False,
                        "error": str(e),
                    }

            # Check if all parameter propagations are correct
            all_propagated = all(
                result.get("all_params_correct", False)
                for result in propagation_results.values()
                if result.get("tested", False)
            )

            test_result.update(
                {
                    "passed": all_propagated,
                    "details": {
                        "propagation_results": propagation_results,
                        "configs_tested": len(test_configs),
                        "configs_with_correct_params": sum(
                            1
                            for r in propagation_results.values()
                            if r.get("all_params_correct", False)
                        ),
                    },
                }
            )

            if not all_propagated:
                test_result["errors"].append(
                    "Some configuration parameters were not properly propagated"
                )

        except Exception as e:
            test_result["errors"].append(f"Parameter propagation test failed: {e}")
            logger.error(f"Parameter propagation error: {e}")

        return test_result

    def _test_feature_activation(self) -> Dict[str, Any]:
        """Test Epic 2 feature activation control."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing feature activation...")

            activation_results = {}

            # Test feature activation for each configuration
            feature_tests = {
                "neural_enabled": {
                    "config_file": "test_epic2_neural_enabled.yaml",
                    "expected_features": {
                        "neural_reranking": True,
                        "graph_enhancement": False,
                    },
                },
                "graph_enabled": {
                    "config_file": "test_epic2_graph_enabled.yaml",
                    "expected_features": {
                        "neural_reranking": False,
                        "graph_enhancement": True,
                    },
                },
                "all_features": {
                    "config_file": "test_epic2_all_features.yaml",
                    "expected_features": {
                        "neural_reranking": True,
                        "graph_enhancement": True,
                    },
                },
                "minimal": {
                    "config_file": "test_epic2_minimal.yaml",
                    "expected_features": {
                        "neural_reranking": False,
                        "graph_enhancement": False,
                    },
                },
            }

            for config_type, feature_test in feature_tests.items():
                try:
                    # Load configuration and create retriever
                    config = self._load_config_file(feature_test["config_file"])

                    factory = ComponentFactory()
                    embedder = factory.create_embedder(
                        config.embedder.type, **config.embedder.config.dict()
                    )
                    retriever = factory.create_retriever(
                        config.retriever.type,
                        embedder=embedder,
                        **config.retriever.config.dict(),
                    )

                    # Check actual feature activation
                    actual_features = {}

                    # Neural reranking feature
                    if isinstance(retriever.reranker, NeuralReranker):
                        actual_features["neural_reranking"] = (
                            retriever.reranker.is_enabled()
                        )
                    else:
                        actual_features["neural_reranking"] = False

                    # Graph enhancement feature
                    if isinstance(retriever.fusion_strategy, GraphEnhancedRRFFusion):
                        actual_features["graph_enhancement"] = getattr(
                            retriever.fusion_strategy, "graph_enabled", True
                        )
                    else:
                        actual_features["graph_enhancement"] = False

                    expected_features = feature_test["expected_features"]

                    # Compare actual vs expected
                    feature_matches = {}
                    for feature, expected in expected_features.items():
                        actual = actual_features.get(feature, False)
                        feature_matches[feature] = actual == expected

                    all_features_correct = all(feature_matches.values())

                    activation_results[config_type] = {
                        "tested": True,
                        "expected_features": expected_features,
                        "actual_features": actual_features,
                        "feature_matches": feature_matches,
                        "all_features_correct": all_features_correct,
                    }

                except Exception as e:
                    activation_results[config_type] = {"tested": False, "error": str(e)}

            # Check if all feature activations are correct
            all_activated_correctly = all(
                result.get("all_features_correct", False)
                for result in activation_results.values()
                if result.get("tested", False)
            )

            test_result.update(
                {
                    "passed": all_activated_correctly,
                    "details": {
                        "activation_results": activation_results,
                        "configs_tested": len(feature_tests),
                        "configs_with_correct_features": sum(
                            1
                            for r in activation_results.values()
                            if r.get("all_features_correct", False)
                        ),
                    },
                }
            )

            if not all_activated_correctly:
                test_result["errors"].append(
                    "Some features were not activated correctly"
                )

        except Exception as e:
            test_result["errors"].append(f"Feature activation test failed: {e}")
            logger.error(f"Feature activation error: {e}")

        return test_result

    def _test_error_handling(self) -> Dict[str, Any]:
        """Test configuration error handling."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing error handling...")

            error_tests = {}

            # Test invalid reranker type
            try:
                invalid_config = {
                    "type": "modular_unified",
                    "config": {
                        "vector_index": {"type": "faiss", "config": {}},
                        "sparse": {"type": "bm25", "config": {}},
                        "fusion": {"type": "rrf", "config": {}},
                        "reranker": {"type": "invalid_type", "config": {}},
                    },
                }

                factory = ComponentFactory()
                # Create dummy embedder
                embedder = Mock()

                # This should raise an error
                factory.create_retriever(
                    "modular_unified", embedder=embedder, **invalid_config["config"]
                )
                error_tests["invalid_reranker"] = {
                    "handled": False,
                    "expected_error": True,
                }

            except Exception:
                error_tests["invalid_reranker"] = {
                    "handled": True,
                    "expected_error": True,
                }

            # Test missing required configuration
            try:
                invalid_config = {
                    "type": "modular_unified",
                    "config": {
                        "vector_index": {"type": "faiss", "config": {}},
                        "sparse": {"type": "bm25", "config": {}},
                        "fusion": {"type": "rrf", "config": {}},
                        # Missing reranker configuration
                    },
                }

                factory = ComponentFactory()
                embedder = Mock()

                # This should raise an error
                factory.create_retriever(
                    "modular_unified", embedder=embedder, **invalid_config["config"]
                )
                error_tests["missing_reranker"] = {
                    "handled": False,
                    "expected_error": True,
                }

            except Exception:
                error_tests["missing_reranker"] = {
                    "handled": True,
                    "expected_error": True,
                }

            # Check if errors were handled correctly
            all_errors_handled = all(
                test.get("handled", False) for test in error_tests.values()
            )

            test_result.update(
                {
                    "passed": all_errors_handled,
                    "details": {
                        "error_tests": error_tests,
                        "error_types_tested": len(error_tests),
                        "errors_handled_correctly": sum(
                            1 for t in error_tests.values() if t.get("handled", False)
                        ),
                    },
                }
            )

            if not all_errors_handled:
                test_result["errors"].append(
                    "Some configuration errors were not handled correctly"
                )

        except Exception as e:
            test_result["errors"].append(f"Error handling test failed: {e}")
            logger.error(f"Error handling test error: {e}")

        return test_result


# Test execution functions for pytest integration
def test_epic2_configuration_validation():
    """Test Epic 2 configuration validation."""
    validator = Epic2ConfigurationValidator()
    results = validator.run_all_validations()

    # Assert overall success
    assert (
        results["overall_score"] > 80
    ), f"Configuration validation failed with score {results['overall_score']}%"
    assert (
        results["passed_tests"] >= 5
    ), f"Only {results['passed_tests']} out of {results['total_tests']} tests passed"

    # Assert specific test categories
    test_results = results["test_results"]

    assert test_results["schema_validation"]["passed"], "Schema validation failed"
    assert test_results["configuration_parsing"][
        "passed"
    ], "Configuration parsing failed"
    assert test_results["subcomponent_instantiation"][
        "passed"
    ], "Sub-component instantiation failed"
    assert test_results["parameter_propagation"][
        "passed"
    ], "Parameter propagation failed"
    assert test_results["feature_activation"]["passed"], "Feature activation failed"
    assert test_results["error_handling"]["passed"], "Error handling failed"


if __name__ == "__main__":
    # Run validation when script is executed directly
    validator = Epic2ConfigurationValidator()
    results = validator.run_all_validations()

    print(f"\n{'='*60}")
    print("EPIC 2 CONFIGURATION VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"Overall Score: {results['overall_score']:.1f}%")
    print(f"Passed Tests: {results['passed_tests']}/{results['total_tests']}")

    if results["overall_score"] >= 90:
        print("✅ EXCELLENT - All configuration validation tests passed!")
    elif results["overall_score"] >= 80:
        print("✅ GOOD - Most configuration validation tests passed")
    else:
        print("❌ NEEDS IMPROVEMENT - Configuration validation issues found")

    # Show detailed results
    for test_name, result in results["test_results"].items():
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result.get("errors"):
            for error in result["errors"]:
                print(f"    - {error}")
